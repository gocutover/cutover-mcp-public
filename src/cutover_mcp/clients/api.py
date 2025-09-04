import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


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
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

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
                if attempt == 2 or (isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500):
                    logger.error("API request failed for %s: %s", url, e)
                    raise
                delay = 2**attempt
                logger.warning("API error for %s: %s. Retrying in %ss", url, e, delay)
                await asyncio.sleep(delay)
        raise ConnectionError("API request failed after multiple retries.")  # Should not be reached


class APIClientManager:
    """
    A small pool to manage APIClient instances, keyed by base_url and api_key.
    This ensures we reuse clients efficiently.
    """

    def __init__(self):
        self._clients: dict[str, APIClient] = {}

    def get_client(self) -> APIClient:
        """Gets a client based on environment variables."""
        base_url = os.getenv("CUTOVER_BASE_URL")
        api_key = os.getenv("CUTOVER_API_TOKEN")
        core_url = os.getenv("CUTOVER_CORE_URL")

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
