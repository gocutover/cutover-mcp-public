import asyncio
import logging
import os
import re
from typing import Any
from urllib.parse import urlparse, urlsplit, urlunsplit

import httpx
from pydantic import BaseModel, Field

from cutover_mcp import __version__
from cutover_mcp.security import host_policy

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.cutover.net"

# Production instances (<name>.cutover.com / .cutover.net) share one API host. Any
# other Cutover environment (<name>.<env>.cutover.cloud) exposes its API at api.<env>.cutover.cloud.
_SHARED_PRODUCTION_DOMAINS = {"cutover.com", "cutover.net"}
_ENVIRONMENT_DOMAIN = "cutover.cloud"
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)

# How each setting is supplied: an env var over stdio, a header on the hosted server.
_CORE_URL_SETTING = "CUTOVER_CORE_URL (or the Core-Url header on the hosted server)"
_BASE_URL_SETTING = "CUTOVER_BASE_URL (or the Base-Url header on the hosted server)"

# Hints added when the API host was derived rather than configured. A wrong host shows
# up as a 401 (that host does not know the token) or as the host failing to serve the
# request at all. A 403 is a valid token without permission and a 400 a bad payload, so
# neither gets a hint: it would steer the client towards configuration instead of the cause.
_DEFAULTED_HOST_AUTH_HINT = (
    "Check that the token is valid for {core_url}. The API host {base_url} was derived from that "
    "instance URL; if your instance has its own API host (single-tenant), set " + _BASE_URL_SETTING + " to it."
)
# Statuses that mean the API host itself could not serve the request (a gateway in
# front of it answered). A 500 means the request reached an API and failed inside it.
_GATEWAY_STATUS_CODES = {502, 503, 504}

# A response body is only worth quoting in an error when it is a short plain message.
# Gateway error pages are HTML and would swamp the error with markup.
_MAX_QUOTED_BODY = 300

_DEFAULTED_HOST_UNREACHABLE_HINT = (
    "The API host {base_url} was derived from the instance URL {core_url} and could not serve the request; "
    "if your instance has its own API host (single-tenant), set " + _BASE_URL_SETTING + " to it."
)


def default_base_url(core_url: str | None) -> str | None:
    """Pick the Cutover API host for ``core_url`` when CUTOVER_BASE_URL is not set.

    Production tenants share one API host; other Cutover environments expose
    theirs at ``api.<environment domain>``. Single-tenant instances have a
    dedicated ``https://api.<instance>`` host and should set CUTOVER_BASE_URL
    explicitly.

    Only the two shapes real instance URLs take are recognised, each with exactly one
    label for the instance name. Anything else (localhost, a customer's own domain, a
    nested subdomain) returns None: guessing there would send the token to an API host
    that was never meant to see it, so the caller must insist on an explicit
    CUTOVER_BASE_URL instead.
    """
    host = (urlparse(core_url).hostname or "").lower() if core_url else ""
    labels = host.split(".")
    if len(labels) == 3 and ".".join(labels[1:]) in _SHARED_PRODUCTION_DOMAINS:
        return DEFAULT_BASE_URL
    if len(labels) == 4 and ".".join(labels[2:]) == _ENVIRONMENT_DOMAIN:
        return f"https://api.{labels[1]}.{_ENVIRONMENT_DOMAIN}"
    return None


def normalise_core_url(core_url: str | None) -> str | None:
    """The instance URL's origin, with the https scheme added when it was dropped.

    A URL copied from a browser bar may lack the scheme and carry the app's ``#/app/...``
    route. public-api requires an absolute Core-Url and reduces it to its origin anyway.
    """
    core_url = (core_url or "").strip()
    if not core_url:
        return None
    if not _SCHEME_RE.match(core_url):
        core_url = f"https://{core_url}"
    try:
        parts = urlsplit(core_url)
    except ValueError:
        return core_url
    if not parts.netloc:
        return None
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


class CutoverCredentials(BaseModel):
    """Requested from the user via an interactive elicitation form (stdio only)."""

    core_url: str = Field(
        description="Your Cutover instance URL. Must be an absolute URL with scheme, "
        "e.g. https://your-instance.cutover.com."
    )
    api_token: str = Field(description="Your personal Cutover API token for that instance.")
    base_url: str = Field(
        default="",
        description="The Cutover API host. Leave blank to use the default for your "
        "instance (https://api.cutover.net for production). Set it only if your "
        "instance has its own API host, e.g. https://api.your-instance.cutover.com.",
    )


class CutoverAPIError(Exception):
    """Raised for Cutover API failures surfaced to the caller as a structured,
    user-facing error: 4xx straight away, 5xx once retries are exhausted.

    ``messages`` carries the parsed error strings from a JSON body so callers
    (e.g. AI tools) can show them instead of the generic ``Client error 'XXX ...'
    for url '...'`` message emitted by ``httpx.HTTPStatusError``. A short plain-text
    body is quoted as is; anything else (a gateway's HTML error page, an empty body)
    collapses to ``HTTP <status> from <url>``. ``raw_body`` always keeps the original.
    """

    def __init__(self, status_code: int, url: str, messages: list[str], raw_body: str = "", hint: str | None = None):
        self.status_code = status_code
        self.url = url
        self.messages = messages
        self.raw_body = raw_body
        self.hint = hint
        if messages:
            detail = "; ".join(messages)
        elif _quotable(raw_body):
            detail = raw_body.strip()
        else:
            detail = f"HTTP {status_code} from {url}"
        if hint:
            detail = f"{detail} {hint}"
        super().__init__(detail)


def _quotable(raw_body: str) -> bool:
    body = raw_body.strip()
    return bool(body) and len(body) <= _MAX_QUOTED_BODY and not body.startswith("<")


class CutoverConnectionError(Exception):
    """Raised when the API host could not be reached after retries.

    Replaces the bare ``httpx.RequestError`` so the message, which is all an MCP client
    sees, can carry the derived-host hint.
    """

    def __init__(self, url: str, cause: Exception, hint: str | None = None):
        self.url = url
        self.hint = hint
        detail = f"Could not reach {url}: {cause}"
        if hint:
            detail = f"{detail} {hint}"
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

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        core_url: str | None = None,
        base_url_defaulted: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.core_url = core_url
        # True when base_url came from default_base_url() rather than config, so
        # errors that smell like a wrong API host can say how to override it.
        self.base_url_defaulted = base_url_defaulted
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create and cache the underlying httpx.AsyncClient."""
        if self._client is None:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": f"CutoverMCP/{__version__}",
                "Authorization": f"Bearer {self.api_key}",
            }
            if self.core_url:
                headers["Core-Url"] = self.core_url
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
                follow_redirects=False,
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
        url = self._url_for(endpoint)
        if host_policy.enforced():
            _logged_check(
                host_policy.check_api_url,
                self.base_url,
                host_policy.trusted_api_hosts(),
                field="API host",
            )
        client = await self._get_client()

        for attempt in range(3):  # Retry logic
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=json_data,
                    params=params,
                )
                response.raise_for_status()
                # A 204, or a 202 that only queues work, has no body.
                return response.json() if response.content else {}
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == 2 or (
                    isinstance(e, httpx.HTTPStatusError)
                    and e.response.status_code < 500
                    and e.response.status_code != 429
                ):
                    if isinstance(e, httpx.HTTPStatusError):
                        status = e.response.status_code
                        logger.warning("API error %s for %s", status, url)
                        raise CutoverAPIError(
                            status_code=status,
                            url=url,
                            messages=_parse_error_messages(e.response),
                            raw_body=e.response.text,
                            hint=self._defaulted_host_hint(status),
                        ) from e
                    logger.error("API request failed for %s: %s", url, e)
                    raise CutoverConnectionError(url, e, hint=self._defaulted_host_hint(None)) from e
                delay = 2**attempt
                logger.warning("API error for %s: %s. Retrying in %ss", url, e, delay)
                await asyncio.sleep(delay)
        raise ConnectionError("API request failed after multiple retries.")  # Should not be reached

    def _url_for(self, endpoint: str) -> str:
        """The URL for ``endpoint`` on this client's API host.

        An absolute URL, such as a ``links.next`` page link from a response, keeps only its
        path and query, so the token is only ever sent to ``base_url``'s host.
        """
        if not endpoint.startswith(("http://", "https://")):
            return f"{self.base_url}/{endpoint.lstrip('/')}"
        link = urlsplit(endpoint)
        base = urlsplit(self.base_url)
        return urlunsplit((base.scheme, base.netloc, link.path, link.query, ""))

    def _defaulted_host_hint(self, status_code: int | None) -> str | None:
        """The override hint for a failure that may stem from a derived API host, else None.

        401: that host does not know the token. 502/503/504 or no response at all: the
        host could not serve the request, e.g. the shared API cannot reach the instance
        behind it. A 500 reached an API and failed inside it, so it gets no hint.
        """
        if not self.base_url_defaulted:
            return None
        if status_code == 401:
            template = _DEFAULTED_HOST_AUTH_HINT
        elif status_code is None or status_code in _GATEWAY_STATUS_CODES:
            template = _DEFAULTED_HOST_UNREACHABLE_HINT
        else:
            return None
        return template.format(base_url=self.base_url, core_url=self.core_url)


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
    # The scheme is case-insensitive (RFC 7235), as in the check that guards /mcp.
    if auth[:7].lower() == "bearer ":
        api_key = auth[7:].strip() or None

    core_url = headers.get("core-url") or None
    base_url = headers.get("base-url") or None
    return api_key, core_url, base_url


async def _credentials_from_elicitation() -> tuple[str | None, str | None, str | None]:
    """Try to obtain (api_key, core_url, base_url) via an interactive client-side form.

    Only used over stdio: a form must not carry a secret over HTTP, where the token
    comes from the Authorization header. Caches an accepted answer in session state so
    the user is only prompted once per session. Returns (None, None, None) outside a
    live session, if the connected client doesn't support elicitation, or if the user
    declines/cancels the prompt.
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
            "Enter your Cutover instance URL and personal API token to continue. "
            "The API host can be left blank unless your instance has its own.",
            CutoverCredentials,
        )
    except Exception:
        logger.warning("Credential elicitation failed or unsupported by client.")
        return None, None, None

    if result.action != "accept":
        return None, None, None

    base_url = result.data.base_url.strip() or None
    await ctx.set_state("cutover_api_key", result.data.api_token)
    await ctx.set_state("cutover_core_url", result.data.core_url)
    await ctx.set_state("cutover_base_url", base_url)
    return result.data.api_token, result.data.core_url, base_url


async def _forget_elicited_credentials() -> None:
    """Drop the credentials form's cached answers so the next call prompts again."""
    try:
        from fastmcp.server.dependencies import get_context

        ctx = get_context()
    except RuntimeError:
        return
    for key in ("cutover_api_key", "cutover_core_url", "cutover_base_url"):
        await ctx.delete_state(key)


def _logged_check(check, *args, **kwargs):
    """Run a host_policy check, logging a rejection under one greppable key."""
    try:
        return check(*args, **kwargs)
    except host_policy.UntrustedHostError as err:
        logger.warning("UNTRUSTED_HOST_REJECTED field=%s reason=%s", err.field[:200], err.reason[:200])
        raise


def _check_api_host(base_url: str, core_url: str | None, base_url_defaulted: bool) -> None:
    """Refuse an API host outside the allowlist."""
    base_field = f"The API host derived from Core-Url {core_url}" if base_url_defaulted else "Base-Url"
    _logged_check(host_policy.check_api_url, base_url, host_policy.trusted_api_hosts(), field=base_field)


def _resolve_api_host(base_url: str | None, core_url: str | None) -> tuple[str, bool]:
    """The API host to call, and whether it was derived from ``core_url`` rather than configured."""
    if base_url:
        return base_url, False
    if not core_url:
        raise ValueError(
            f"Set {_CORE_URL_SETTING} to your Cutover instance URL, e.g. https://your-instance.cutover.com, "
            f"or {_BASE_URL_SETTING} if your instance has its own API host."
        )
    derived = default_base_url(core_url)
    if derived is None:
        raise ValueError(
            f"Cannot derive the Cutover API host from the instance URL {core_url}: it is not a "
            f"Cutover-hosted instance URL. Set {_BASE_URL_SETTING} explicitly, "
            "e.g. http://localhost:9292 for a local public-api."
        )
    return derived, True


class APIClientManager:
    """
    A small pool to manage APIClient instances, keyed by base_url and api_key.
    This ensures we reuse clients efficiently.

    When running over streamable-http, the Cutover API token, Core-Url, and
    Base-Url are read from the incoming request's Authorization / Core-Url /
    Base-Url headers (per-user, so a single deployment can serve sessions
    targeting different Cutover environments). The token only ever comes from
    the header there: no shared CUTOVER_API_TOKEN and no credentials form.
    Over stdio the env vars are used, and as a last resort the connected client
    is prompted interactively (session-cached) if it supports elicitation.

    The base URL is optional everywhere: when absent it is derived from the
    Core-Url with default_base_url(), so shared production tenants only need
    an instance URL and a token.
    """

    def __init__(self):
        self._clients: dict[str, APIClient] = {}

    async def get_client(self) -> APIClient:
        """Gets a client, preferring per-request HTTP credentials over env vars."""
        over_http = host_policy.enforced()
        header_api_key, header_core_url, header_base_url = _credentials_from_http_headers()
        # Over HTTP the token is the caller's own: never the server's, never asked for in a form.
        api_key = header_api_key
        if not api_key and not over_http:
            api_key = os.getenv("CUTOVER_API_TOKEN") or None
        supplied_core_url = header_core_url or os.getenv("CUTOVER_CORE_URL")
        core_url = normalise_core_url(supplied_core_url)
        base_url = header_base_url or os.getenv("CUTOVER_BASE_URL") or None

        from_form = False
        if not api_key and not over_http:
            elicited_key, elicited_core_url, elicited_base_url = await _credentials_from_elicitation()
            if elicited_key:
                api_key = elicited_key
                from_form = True
                if not core_url:
                    supplied_core_url = elicited_core_url or supplied_core_url
                    core_url = normalise_core_url(elicited_core_url)
                base_url = base_url or elicited_base_url

        if not api_key:
            if over_http:
                raise ValueError("Send your Cutover API token as an Authorization: Bearer header.")
            raise ValueError("CUTOVER_API_TOKEN must be set (or sent as an Authorization: Bearer header).")

        try:
            # A supplied instance URL with no origin (e.g. "https://") normalises to None; check what
            # was supplied so it is refused instead of being dropped.
            checked_core_url = core_url or (supplied_core_url or "").strip()
            if over_http and checked_core_url:
                _logged_check(host_policy.check_core_url, checked_core_url)
            base_url, base_url_defaulted = _resolve_api_host(base_url, core_url)
            if over_http:
                _check_api_host(base_url, core_url, base_url_defaulted)
        except ValueError:
            if from_form:
                await _forget_elicited_credentials()
            raise

        # base_url_defaulted is part of the key: the same host reached explicitly and by
        # default must not share a client, or the override hint would be wrong for one.
        key = f"{base_url}|{api_key}|{core_url}|{base_url_defaulted}"
        if key not in self._clients:
            if base_url_defaulted:
                logger.info("No API host configured; derived %s from the instance URL %s", base_url, core_url)
            self._clients[key] = APIClient(base_url, api_key, core_url=core_url, base_url_defaulted=base_url_defaulted)
        return self._clients[key]

    async def close_all(self) -> None:
        """Closes all managed client sessions."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()


# Singleton instance used throughout the application
client_mgr = APIClientManager()
