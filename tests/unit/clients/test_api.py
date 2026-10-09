import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from cutover_mcp.clients.api import (
    APIClient,
    APIClientManager,
    CutoverAPIError,
    CutoverConnectionError,
    CutoverCredentials,
    _credentials_from_elicitation,
    default_base_url,
)


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
                base_url="https://api.sandbox.cutover.cloud",
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
        "https://api.sandbox.cutover.cloud",
    )
    ctx.set_state.assert_any_await("cutover_api_key", "new-token")
    ctx.set_state.assert_any_await("cutover_core_url", "https://team.cutover.com")
    ctx.set_state.assert_any_await("cutover_base_url", "https://api.sandbox.cutover.cloud")


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
async def test_5xx_is_retried_then_raised_as_cutover_api_error(monkeypatch):
    """5xx errors are retried; once retries are exhausted they are wrapped like any other
    failure, so the message (all an MCP client sees) can carry the parsed body and hints."""
    client = APIClient(base_url="https://api.example.com", api_key="token")

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.example.com") as mock:
        route = mock.get("/widgets/1").mock(return_value=httpx.Response(503, json={"error": "service unavailable"}))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    assert route.call_count == 3
    assert exc_info.value.status_code == 503
    assert exc_info.value.hint is None
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


@pytest.mark.parametrize(
    ("core_url", "expected"),
    [
        ("https://your-instance.cutover.com", "https://api.cutover.net"),
        ("https://your-instance.cutover.net", "https://api.cutover.net"),
        ("https://your-instance.sandbox.cutover.cloud", "https://api.sandbox.cutover.cloud"),
        ("https://your-instance.preview.cutover.cloud/", "https://api.preview.cutover.cloud"),
        ("HTTPS://YOUR-INSTANCE.SANDBOX.CUTOVER.CLOUD", "https://api.sandbox.cutover.cloud"),
        ("http://localhost:3000", None),
        ("https://core.example.org", None),
        ("https://your-instance.cutover.cloud", None),
        ("https://foo.bar.cutover.com", None),
        ("https://x.y.sandbox.cutover.cloud", None),
        (None, None),
    ],
)
def test_default_base_url_is_derived_from_the_instance_host(core_url, expected):
    assert default_base_url(core_url) == expected


@pytest.mark.asyncio
async def test_get_client_defaults_base_url_from_core_url(monkeypatch):
    """Shared production tenants only need an instance URL and a token."""
    monkeypatch.delenv("CUTOVER_BASE_URL", raising=False)
    monkeypatch.setenv("CUTOVER_CORE_URL", "https://your-instance.cutover.com")
    monkeypatch.setenv("CUTOVER_API_TOKEN", "token")
    mgr = APIClientManager()

    client = await mgr.get_client()

    assert client.base_url == "https://api.cutover.net"
    assert client.core_url == "https://your-instance.cutover.com"
    assert client.base_url_defaulted is True
    await mgr.close_all()


@pytest.mark.asyncio
async def test_get_client_prefers_an_explicit_base_url(monkeypatch):
    monkeypatch.setenv("CUTOVER_BASE_URL", "https://api.your-instance.cutover.com")
    monkeypatch.setenv("CUTOVER_CORE_URL", "https://your-instance.cutover.com")
    monkeypatch.setenv("CUTOVER_API_TOKEN", "token")
    mgr = APIClientManager()

    client = await mgr.get_client()

    assert client.base_url == "https://api.your-instance.cutover.com"
    assert client.base_url_defaulted is False
    await mgr.close_all()


@pytest.mark.asyncio
async def test_get_client_accepts_a_base_url_without_core_url(monkeypatch):
    """Local public-api and single-tenant API hosts identify the instance on their own."""
    monkeypatch.setenv("CUTOVER_BASE_URL", "http://localhost:9292")
    monkeypatch.setenv("CUTOVER_CORE_URL", "")
    monkeypatch.setenv("CUTOVER_API_TOKEN", "development-token")
    mgr = APIClientManager()

    client = await mgr.get_client()

    assert client.base_url == "http://localhost:9292"
    assert client.core_url is None
    await mgr.close_all()


@pytest.mark.asyncio
async def test_get_client_requires_an_instance_or_api_host(monkeypatch):
    monkeypatch.delenv("CUTOVER_BASE_URL", raising=False)
    monkeypatch.delenv("CUTOVER_CORE_URL", raising=False)
    monkeypatch.setenv("CUTOVER_API_TOKEN", "token")

    with pytest.raises(ValueError, match="CUTOVER_CORE_URL"):
        await APIClientManager().get_client()


@pytest.mark.asyncio
async def test_get_client_requires_a_token(monkeypatch):
    monkeypatch.delenv("CUTOVER_BASE_URL", raising=False)
    monkeypatch.setenv("CUTOVER_CORE_URL", "https://your-instance.cutover.com")
    monkeypatch.delenv("CUTOVER_API_TOKEN", raising=False)
    no_elicitation = AsyncMock(return_value=(None, None, None))

    with (
        patch("cutover_mcp.clients.api._credentials_from_elicitation", no_elicitation),
        pytest.raises(ValueError, match="CUTOVER_API_TOKEN"),
    ):
        await APIClientManager().get_client()


@pytest.mark.asyncio
async def test_auth_errors_mention_the_defaulted_base_url():
    """A 401 on a defaulted base URL may mean a single-tenant host; say how to override."""
    client = APIClient(
        "https://api.cutover.net", "token", core_url="https://your-instance.cutover.com", base_url_defaulted=True
    )

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/core/users/me").mock(
            return_value=httpx.Response(401, json={"errors": [{"detail": "Authorized users only."}]})
        )

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "core/users/me")

    assert exc_info.value.messages[0] == "Authorized users only."
    assert "CUTOVER_BASE_URL" in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_business_errors_do_not_mention_the_base_url():
    """A 422 is about the payload, not the host, even when the base URL was defaulted."""
    client = APIClient("https://api.cutover.net", "token", base_url_defaulted=True)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(422, json={"errors": [{"detail": "name is required"}]}))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    assert exc_info.value.messages == ["name is required"]
    await client.aclose()


@pytest.mark.asyncio
async def test_elicitation_treats_a_blank_base_url_as_unset():
    """The form's API host field is optional; blank means 'derive it from the instance URL'."""
    ctx = _mock_context(
        get_state_side_effect=[None, None, None],
        elicit_return_value=MagicMock(
            action="accept",
            data=CutoverCredentials(core_url="https://your-instance.cutover.com", api_token="new-token"),
        ),
    )

    with patch("fastmcp.server.dependencies.get_context", return_value=ctx):
        api_key, core_url, base_url = await _credentials_from_elicitation()

    assert (api_key, core_url, base_url) == ("new-token", "https://your-instance.cutover.com", None)
    ctx.set_state.assert_any_await("cutover_base_url", None)


@pytest.mark.asyncio
async def test_hint_keeps_the_raw_body_when_the_error_is_not_json():
    """The override hint is added to the message, never in place of the API's own error."""
    client = APIClient("https://api.cutover.net", "token", base_url_defaulted=True)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(401, text="Unauthorized: token rejected"))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    err = exc_info.value
    assert err.messages == []
    assert err.raw_body == "Unauthorized: token rejected"
    assert "Unauthorized: token rejected" in str(err)
    assert "CUTOVER_BASE_URL" in str(err)
    await client.aclose()


@pytest.mark.asyncio
async def test_hint_falls_back_to_the_status_when_the_body_is_empty():
    client = APIClient("https://api.cutover.net", "token", base_url_defaulted=True)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(401))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    assert str(exc_info.value).startswith("HTTP 401")
    assert "CUTOVER_BASE_URL" in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_cached_client_is_not_shared_between_explicit_and_defaulted_base_url(monkeypatch):
    """Same host, token and instance, but one request configured the host and the other
    relied on the default: they must not share a client, or the hint would be wrong."""
    monkeypatch.setenv("CUTOVER_BASE_URL", "https://api.cutover.net")
    monkeypatch.setenv("CUTOVER_CORE_URL", "https://your-instance.cutover.com")
    monkeypatch.setenv("CUTOVER_API_TOKEN", "token")
    mgr = APIClientManager()

    explicit = await mgr.get_client()
    monkeypatch.delenv("CUTOVER_BASE_URL")
    defaulted = await mgr.get_client()

    assert explicit is not defaulted
    assert explicit.base_url == defaulted.base_url == "https://api.cutover.net"
    assert explicit.base_url_defaulted is False
    assert defaulted.base_url_defaulted is True
    await mgr.close_all()


@pytest.mark.asyncio
async def test_validation_400_does_not_mention_the_base_url():
    """400 is the API's answer to a malformed payload; the client should fix the
    request, not its configuration, so no host hint even on a defaulted base URL."""
    client = APIClient("https://api.cutover.net", "token", base_url_defaulted=True)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.post("/core/runbooks").mock(
            return_value=httpx.Response(
                400, json={"errors": [{"detail": "did not contain a required property of 'custom_field_id'"}]}
            )
        )

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("POST", "core/runbooks", json_data={})

    assert "custom_field_id" in str(exc_info.value)
    assert "CUTOVER_BASE_URL" not in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_client_refuses_to_guess_the_host_for_a_non_cutover_instance(monkeypatch):
    """A local core or a customer's own domain must not have its token sent to the
    production API by default."""
    monkeypatch.delenv("CUTOVER_BASE_URL", raising=False)
    monkeypatch.setenv("CUTOVER_CORE_URL", "http://localhost:3000")
    monkeypatch.setenv("CUTOVER_API_TOKEN", "development-token")

    with pytest.raises(ValueError, match="CUTOVER_BASE_URL") as exc_info:
        await APIClientManager().get_client()

    assert "localhost:3000" in str(exc_info.value)


@pytest.mark.asyncio
async def test_401_hint_puts_the_token_first_and_names_the_header():
    client = APIClient(
        "https://api.cutover.net", "token", core_url="https://your-instance.cutover.com", base_url_defaulted=True
    )

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/core/users/me").mock(
            return_value=httpx.Response(401, json={"errors": [{"detail": "Authorized users only."}]})
        )

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "core/users/me")

    text = str(exc_info.value)
    assert text.startswith("Authorized users only. Check that the token is valid for https://your-instance.cutover.com")
    assert "Base-Url header" in text
    await client.aclose()


@pytest.mark.asyncio
async def test_403_does_not_mention_the_base_url():
    """A 403 is a valid token without permission, not a wrong host."""
    client = APIClient("https://api.cutover.net", "token", base_url_defaulted=True)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(403, json={"errors": ["Forbidden"]}))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    assert str(exc_info.value) == "Forbidden"
    await client.aclose()


@pytest.mark.asyncio
async def test_5xx_on_a_derived_host_carries_the_hint_in_the_message(monkeypatch):
    client = APIClient(
        "https://api.cutover.net", "token", core_url="https://your-instance.cutover.com", base_url_defaulted=True
    )

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(503, json={"errors": ["Core unavailable"]}))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    text = str(exc_info.value)
    assert text.startswith("Core unavailable")
    assert "derived from the instance URL https://your-instance.cutover.com" in text
    assert "Base-Url header" in text
    await client.aclose()


@pytest.mark.asyncio
async def test_connection_failure_on_a_derived_host_carries_the_hint_in_the_message(monkeypatch):
    client = APIClient(
        "https://api.cutover.net", "token", core_url="https://your-instance.cutover.com", base_url_defaulted=True
    )

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        route = mock.get("/widgets/1").mock(side_effect=httpx.ConnectError("connection refused"))

        with pytest.raises(CutoverConnectionError) as exc_info:
            await client.request("GET", "widgets/1")

    assert route.call_count == 3
    text = str(exc_info.value)
    assert text.startswith("Could not reach https://api.cutover.net/widgets/1: connection refused")
    assert "Base-Url header" in text
    await client.aclose()


@pytest.mark.asyncio
async def test_connection_failure_without_a_derived_host_has_no_hint(monkeypatch):
    client = APIClient("https://api.example.com", "token")

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.example.com") as mock:
        mock.get("/widgets/1").mock(side_effect=httpx.ConnectError("connection refused"))

        with pytest.raises(CutoverConnectionError) as exc_info:
            await client.request("GET", "widgets/1")

    assert exc_info.value.hint is None
    assert "Base-Url" not in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_client_adds_the_scheme_to_a_bare_instance_hostname(monkeypatch):
    """A browser bar hides the scheme; a copied hostname should still derive the host."""
    monkeypatch.delenv("CUTOVER_BASE_URL", raising=False)
    monkeypatch.setenv("CUTOVER_CORE_URL", "your-instance.cutover.com")
    monkeypatch.setenv("CUTOVER_API_TOKEN", "token")
    mgr = APIClientManager()

    client = await mgr.get_client()

    assert client.core_url == "https://your-instance.cutover.com"
    assert client.base_url == "https://api.cutover.net"
    await mgr.close_all()


@pytest.mark.asyncio
async def test_configuration_errors_name_the_hosted_server_headers(monkeypatch):
    monkeypatch.delenv("CUTOVER_BASE_URL", raising=False)
    monkeypatch.delenv("CUTOVER_CORE_URL", raising=False)
    monkeypatch.setenv("CUTOVER_API_TOKEN", "token")

    with pytest.raises(ValueError, match="Core-Url header"):
        await APIClientManager().get_client()

    monkeypatch.setenv("CUTOVER_CORE_URL", "http://localhost:3000")

    with pytest.raises(ValueError, match="Base-Url header"):
        await APIClientManager().get_client()


@pytest.mark.asyncio
async def test_derived_host_is_logged_once_per_client(monkeypatch, caplog):
    monkeypatch.delenv("CUTOVER_BASE_URL", raising=False)
    monkeypatch.setenv("CUTOVER_CORE_URL", "https://your-instance.cutover.com")
    monkeypatch.setenv("CUTOVER_API_TOKEN", "token")
    mgr = APIClientManager()

    with caplog.at_level(logging.INFO, logger="cutover_mcp.clients.api"):
        await mgr.get_client()
        await mgr.get_client()

    assert sum("derived https://api.cutover.net" in r.getMessage() for r in caplog.records) == 1
    await mgr.close_all()


_GATEWAY_HTML = (
    "<!DOCTYPE html><html><head><title>502 Bad Gateway</title></head><body>" + "<p>upstream</p>" * 60 + "</body></html>"
)


@pytest.mark.asyncio
async def test_html_gateway_page_collapses_to_a_short_message(monkeypatch):
    """A 502/503 from the gateway in front of the API is an HTML page; the error must
    not quote it, for every user, derived host or not."""
    client = APIClient("https://api.example.com", "token")

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.example.com") as mock:
        mock.get("/widgets/1").mock(
            return_value=httpx.Response(502, text=_GATEWAY_HTML, headers={"content-type": "text/html"})
        )

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    err = exc_info.value
    assert str(err) == "HTTP 502 from https://api.example.com/widgets/1"
    assert err.raw_body == _GATEWAY_HTML
    await client.aclose()


@pytest.mark.asyncio
async def test_html_gateway_page_on_a_derived_host_keeps_the_hint_readable(monkeypatch):
    client = APIClient(
        "https://api.cutover.net", "token", core_url="https://your-instance.cutover.com", base_url_defaulted=True
    )

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/widgets/1").mock(
            return_value=httpx.Response(503, text=_GATEWAY_HTML, headers={"content-type": "text/html"})
        )

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    text = str(exc_info.value)
    assert text.startswith("HTTP 503 from https://api.cutover.net/widgets/1 The API host")
    assert "Base-Url header" in text
    assert "<html" not in text
    await client.aclose()


@pytest.mark.asyncio
async def test_500_on_a_derived_host_has_no_hint(monkeypatch):
    """A 500 reached an API and failed inside it; that is not a host problem."""
    client = APIClient(
        "https://api.cutover.net", "token", core_url="https://your-instance.cutover.com", base_url_defaulted=True
    )

    async def no_sleep(_delay):
        return None

    monkeypatch.setattr("cutover_mcp.clients.api.asyncio.sleep", no_sleep)

    with respx.mock(base_url="https://api.cutover.net") as mock:
        mock.get("/widgets/1").mock(return_value=httpx.Response(500, json={"errors": ["boom"]}))

        with pytest.raises(CutoverAPIError) as exc_info:
            await client.request("GET", "widgets/1")

    assert str(exc_info.value) == "boom"
    assert exc_info.value.hint is None
    await client.aclose()
