import httpx
import pytest
import respx

from cutover_mcp.clients.api import APIClient, CutoverAPIError


@pytest.mark.asyncio
async def test_request_error_includes_json_response_body():
    """A non-retryable 4xx error should surface the parsed JSON:API error detail."""
    client = APIClient(base_url="https://api.example.com", api_key="token")

    with respx.mock(base_url="https://api.example.com") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(422, json={"errors": [{"detail": "name is required"}]}))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    err = exc_info.value
    assert err.status_code == 422
    assert err.messages == ["name is required"]
    assert "name is required" in str(err)
    await client.aclose()


@pytest.mark.asyncio
async def test_request_error_falls_back_to_raw_body_when_unparseable():
    """Falls back to the raw text body when the response isn't JSON."""
    client = APIClient(base_url="https://api.example.com", api_key="token")

    with respx.mock(base_url="https://api.example.com") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(400, text="Bad Request: malformed query"))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    err = exc_info.value
    assert err.messages == []
    assert err.raw_body == "Bad Request: malformed query"
    assert "Bad Request: malformed query" in str(err)
    await client.aclose()


@pytest.mark.asyncio
async def test_5xx_still_raises_bare_http_status_error(monkeypatch):
    """5xx errors are retryable, not deterministic client mistakes, so they keep
    propagating as httpx.HTTPStatusError rather than being wrapped."""
    client = APIClient(base_url="https://api.example.com", api_key="token")

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.example.com") as mock:
        route = mock.get("/widgets/1").mock(return_value=httpx.Response(503, json={"error": "service unavailable"}))

        with pytest.raises(httpx.HTTPStatusError):
            await client.request("GET", "widgets/1")

    assert route.call_count == 3
    await client.aclose()


@pytest.mark.asyncio
async def test_retryable_429_eventually_raises_cutover_api_error(monkeypatch):
    """429 is retried, but once retries are exhausted it's still a 4xx so it's
    wrapped in CutoverAPIError with the parsed body."""
    client = APIClient(base_url="https://api.example.com", api_key="token")

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.example.com") as mock:
        route = mock.get("/widgets/1").mock(return_value=httpx.Response(429, json={"errors": ["rate limited"]}))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    assert route.call_count == 3
    assert exc_info.value.status_code == 429
    assert exc_info.value.messages == ["rate limited"]
    await client.aclose()
