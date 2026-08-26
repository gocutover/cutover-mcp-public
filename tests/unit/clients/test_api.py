from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from cutover_mcp.clients.api import APIClient, CutoverAPIError, CutoverCredentials, _credentials_from_elicitation


def _mock_context(get_state_side_effect=None, elicit_return_value=None, elicit_side_effect=None):
    ctx = MagicMock()
    ctx.get_state = AsyncMock(side_effect=get_state_side_effect)
    ctx.set_state = AsyncMock()
    ctx.elicit = AsyncMock(return_value=elicit_return_value, side_effect=elicit_side_effect)
    return ctx


@pytest.mark.asyncio
async def test_returns_none_outside_a_live_session():
    """No MCP session (e.g. stdio outside a request) -> get_context() raises RuntimeError."""
    with patch("fastmcp.server.dependencies.get_context", side_effect=RuntimeError):
        api_key, core_url, base_url = await _credentials_from_elicitation()

    assert (api_key, core_url, base_url) == (None, None, None)


@pytest.mark.asyncio
async def test_uses_cached_credentials_without_re_eliciting():
    """A cache hit must await get_state and skip elicit() entirely."""
    ctx = _mock_context(
        get_state_side_effect=["cached-token", "https://cached.cutover.com", "https://api.cached.cutover.cloud"]
    )

    with patch("fastmcp.server.dependencies.get_context", return_value=ctx):
        api_key, core_url, base_url = await _credentials_from_elicitation()

    assert (api_key, core_url, base_url) == (
        "cached-token",
        "https://cached.cutover.com",
        "https://api.cached.cutover.cloud",
    )
    ctx.elicit.assert_not_called()


@pytest.mark.asyncio
async def test_elicits_and_caches_on_accept():
    """No cached value -> elicit() is called and an accepted answer is cached via set_state."""
    ctx = _mock_context(
        get_state_side_effect=[None, None, None],
        elicit_return_value=MagicMock(
            action="accept",
            data=CutoverCredentials(
                base_url="https://api.dev.cutover.cloud",
                core_url="https://team.cutover.com",
                api_token="new-token",
            ),
        ),
    )

    with patch("fastmcp.server.dependencies.get_context", return_value=ctx):
        api_key, core_url, base_url = await _credentials_from_elicitation()

    assert (api_key, core_url, base_url) == (
        "new-token",
        "https://team.cutover.com",
        "https://api.dev.cutover.cloud",
    )
    ctx.set_state.assert_any_await("cutover_api_key", "new-token")
    ctx.set_state.assert_any_await("cutover_core_url", "https://team.cutover.com")
    ctx.set_state.assert_any_await("cutover_base_url", "https://api.dev.cutover.cloud")


@pytest.mark.asyncio
async def test_returns_none_when_user_declines():
    """Declined/cancelled elicitation must not be cached."""
    ctx = _mock_context(
        get_state_side_effect=[None, None, None],
        elicit_return_value=MagicMock(action="decline", data=None),
    )

    with patch("fastmcp.server.dependencies.get_context", return_value=ctx):
        api_key, core_url, base_url = await _credentials_from_elicitation()

    assert (api_key, core_url, base_url) == (None, None, None)
    ctx.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_returns_none_when_client_does_not_support_elicitation():
    """elicit() raising (e.g. unsupported client) must fall back cleanly, not propagate."""
    ctx = _mock_context(get_state_side_effect=[None, None, None], elicit_side_effect=Exception("unsupported"))

    with patch("fastmcp.server.dependencies.get_context", return_value=ctx):
        api_key, core_url, base_url = await _credentials_from_elicitation()

    assert (api_key, core_url, base_url) == (None, None, None)


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
