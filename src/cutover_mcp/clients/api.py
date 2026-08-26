import asyncio
import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CutoverCredentials(BaseModel):
    """Requested from the user via an interactive elicitation form."""

    base_url: str = Field(
        description="The Cutover API endpoint for your environment, e.g. "
        "https://api.cutover.com."
    )
    core_url: str = Field(
        description="The Cutover server URL you want to connect to. Must be an "
        "absolute URL with scheme, e.g. https://your-instance.cutover.com."
    )
    api_token: str = Field(description="Your personal Cutover API token for that server.")


class CutoverAPIError(Exception):
    """Raised for Cutover API failures that should be surfaced to the caller as a
    structured, user-facing error rather than retried as a transient fault.

    ``messages`` carries the parsed user-facing error strings from the response
    body so callers (e.g. AI tools) can surface them to the user instead of the
    generic ``Client error 'XXX ...' for url '...'`` message emitted by
    ``httpx.HTTPStatusError``.
    """

    def __init__(self, status_code: int, url: str, messages: list[str], raw_body: str = ""):
        self.status_code = status_code
        self.url = url
        self.messages = messages
        self.raw_body = raw_body
        detail = "; ".join(messages) if messages else raw_body or f"HTTP {status_code}"
        super().__init__(detail)


def _parse_error_messages(response: httpx.Response) -> list[str]:
    """Best-effort extraction of user-facing error strings from a Cutover/public API
    response body. Supports both the common ``{"errors": [...]}`` shape and
    JSON:API-style ``{"errors": [{"title": ..., "detail": ...}]}``.
    """
    try:
        payload = response.json()
    except (ValueError, httpx.DecodingError):
        return []

    if not isinstance(payload, dict):
        return []

    errors = payload.get("errors") or payload.get("error")
    if errors is None:
        detail = payload.get("detail") or payload.get("message")
        return [str(detail)] if detail else []

    if isinstance(errors, str):
        return [errors]

    if isinstance(errors, list):
        messages: list[str] = []
        for item in errors:
            if isinstance(item, str):
                messages.append(item)
            elif isinstance(item, dict):
                messages.append(str(item.get("detail") or item.get("title") or item.get("message") or item))
        return messages

    return []


class APIClient:
    """
    A thin convenience wrapper around one shared httpx.AsyncClient.
    This class should not be instantiated directly; use the client_mgr.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0, core_url: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.core_url = core_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create and cache the underlying httpx.AsyncClient."""
        if self._client is None:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "CutoverMCP/0.3.0",
                "Authorization": f"Bearer {self.api_key}",
            }
            if self.core_url:
                headers["Core-Url"] = self.core_url
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
            )
        return self._client

    async def aclose(self) -> None:
        """Close the client session if it exists."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with opinionated error handling."""
        client = await self._get_client()
        url = endpoint if endpoint.startswith(("http://", "https://")) else f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(3):  # Retry logic
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=json_data,
                    params=params,
                )
                response.raise_for_status()
                # Return empty dict for 204 No Content responses
                return response.json() if response.status_code != 204 else {}
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == 2 or (
                    isinstance(e, httpx.HTTPStatusError)
                    and 400 <= e.response.status_code < 500
                    and e.response.status_code != 429
                ):
                    if isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500:
                        logger.warning("API client error for %s: %s", url, e.response.text)
                        raise CutoverAPIError(
                            status_code=e.response.status_code,
                            url=url,
                            messages=_parse_error_messages(e.response),
                            raw_body=e.response.text,
                        ) from e
                    logger.error("API request failed for %s: %s", url, e)
                    raise
                delay = 2**attempt
                logger.warning("API error for %s: %s. Retrying in %ss", url, e, delay)
                await asyncio.sleep(delay)
        raise ConnectionError("API request failed after multiple retries.")  # Should not be reached


def _credentials_from_http_headers() -> tuple[str | None, str | None, str | None]:
    """Try to extract (api_key, core_url, base_url) from the current HTTP request's headers.

    Returns (None, None, None) outside an HTTP request context (e.g. stdio transport).
    """
    try:
        from fastmcp.server.dependencies import get_http_request

        headers = get_http_request().headers
    except Exception:
        return None, None, None

    api_key = None
    auth = headers.get("authorization", "")
    if auth.startswith("Bearer "):
        api_key = auth.removeprefix("Bearer ").strip()

    core_url = headers.get("core-url") or None
    base_url = headers.get("base-url") or None
    return api_key, core_url, base_url


async def _credentials_from_elicitation() -> tuple[str | None, str | None, str | None]:
    """Try to obtain (api_key, core_url, base_url) via an interactive client-side form.

    Caches an accepted answer in session state so the user is only prompted
    once per session. Returns (None, None, None) outside a live session (e.g.
    stdio), if the connected client doesn't support elicitation, or if the
    user declines/cancels the prompt.
    """
    try:
        from fastmcp.server.dependencies import get_context

        ctx = get_context()
    except RuntimeError:
        return None, None, None

    cached_key = await ctx.get_state("cutover_api_key")
    cached_url = await ctx.get_state("cutover_core_url")
    cached_base_url = await ctx.get_state("cutover_base_url")
    if cached_key:
        return cached_key, cached_url, cached_base_url

    try:
        result = await ctx.elicit(
            "Enter the Cutover API endpoint, server URL, and your personal API token to continue.",
            CutoverCredentials,
        )
    except Exception:
        logger.warning("Credential elicitation failed or unsupported by client.")
        return None, None, None

    if result.action != "accept":
        return None, None, None

    await ctx.set_state("cutover_api_key", result.data.api_token)
    await ctx.set_state("cutover_core_url", result.data.core_url)
    await ctx.set_state("cutover_base_url", result.data.base_url)
    return result.data.api_token, result.data.core_url, result.data.base_url


class APIClientManager:
    """
    A small pool to manage APIClient instances, keyed by base_url and api_key.
    This ensures we reuse clients efficiently.

    When running over streamable-http, the Cutover API token, Core-Url, and
    Base-Url are read from the incoming request's Authorization / Core-Url /
    Base-Url headers (per-user, so a single deployment can serve sessions
    targeting different Cutover environments). Falls back to env vars for
    stdio / local development, and as a last resort prompts the connected
    client interactively (session-cached) if it supports elicitation.
    """

    def __init__(self):
        self._clients: dict[str, APIClient] = {}

    async def get_client(self) -> APIClient:
        """Gets a client, preferring per-request HTTP credentials over env vars."""
        header_api_key, header_core_url, header_base_url = _credentials_from_http_headers()
        api_key = header_api_key or os.getenv("CUTOVER_API_TOKEN")
        core_url = header_core_url or os.getenv("CUTOVER_CORE_URL")
        base_url = header_base_url or os.getenv("CUTOVER_BASE_URL")

        if not api_key:
            elicited_key, elicited_core_url, elicited_base_url = await _credentials_from_elicitation()
            if elicited_key:
                api_key = elicited_key
                core_url = core_url or elicited_core_url
                base_url = base_url or elicited_base_url

        if not base_url or not api_key:
            raise ValueError("CUTOVER_BASE_URL and CUTOVER_API_TOKEN must be set.")

        key = f"{base_url}|{api_key}|{core_url}"
        if key not in self._clients:
            self._clients[key] = APIClient(base_url, api_key, core_url=core_url)
        return self._clients[key]

    async def close_all(self) -> None:
        """Closes all managed client sessions."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()


# Singleton instance used throughout the application
client_mgr = APIClientManager()
