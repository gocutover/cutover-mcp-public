from unittest.mock import patch

import pytest

from cutover_mcp.security.host_policy import (
    DEFAULT_TRUSTED_API_HOSTS,
    UntrustedHostError,
    check_api_url,
    check_core_url,
    enforced,
    parse_trusted_api_hosts,
    trusted_api_hosts,
)

DEFAULT = parse_trusted_api_hosts(DEFAULT_TRUSTED_API_HOSTS)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.cutover.net",
        "https://api.cutover.net/",
        "https://API.CUTOVER.NET",
        "https://api.cutover.net:443",
        "https://api.acme.cutover.com",
        "https://api.dev.cutover.cloud",
        "https://api.staging.cutover.cloud",
        "https://api.preview.cutover.dev",
    ],
)
def test_default_list_trusts_prod_environment_and_preview_api_hosts(url):
    assert check_api_url(url, DEFAULT, field="Base-Url") == url


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1",
        "https://10.0.0.1",
        "https://[::1]",
        "http://api.cutover.net",
        "https://api.cutover.net:8443",
        "https://api.cutover.net.evil.com",
        "https://evil.com#.cutover.net",
        "https://x@api.cutover.net",
        "https://api.cutover.net\\@evil.com",
        "https://api.cutover.net\t",
        "https://api.cutover.net.",
        "https://api.cutover.net?next=/x",
        "https://api.internal.cutover.com",
        "https://api.corp.cutover.com",
        "https://api.a.b.cutover.com",
        "https://acme.cutover.com",
        "https://api.internal.cutover.cloud",
        "https://api.corp.cutover.cloud",
        "https://x.internal.example.cutover.cloud",
        "https://some-service.corp.cutover.cloud",
        "https://api.cutover.cloud",
        "https://api.a.b.cutover.cloud",
        "https://your-instance.dev.cutover.cloud",
        "ftp://api.cutover.net",
        "api.cutover.net",
        "",
        None,
    ],
)
def test_default_list_refuses_anything_else(url):
    with pytest.raises(UntrustedHostError):
        check_api_url(url, DEFAULT, field="Base-Url")


def test_an_exact_entry_can_name_a_host_in_an_internal_zone():
    trusted = parse_trusted_api_hosts("api.internal.example.cutover.cloud")
    url = "https://api.internal.example.cutover.cloud"
    assert check_api_url(url, trusted, field="Base-Url") == url


def test_rejection_names_the_field_and_the_host():
    with pytest.raises(UntrustedHostError, match=r"Base-Url is not allowed: 'evil\.example' is not a trusted"):
        check_api_url("https://evil.example", DEFAULT, field="Base-Url")


@pytest.mark.parametrize(
    "raw",
    [
        "*.com",
        "api.*",
        "api.cutover.*",
        "cutover",
        "10.0.0.1",
        "https://api.cutover.net",
        "api.cutover.net:8443",
        "api..cutover.net",
        "api.cut over.net",
        "api.cutover.net/path",
        ",",
    ],
)
def test_malformed_entries_raise(raw):
    with pytest.raises(ValueError, match="TRUSTED_API_HOSTS"):
        parse_trusted_api_hosts(raw)


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_unset_or_blank_means_the_default_list(monkeypatch, raw):
    if raw is None:
        monkeypatch.delenv("TRUSTED_API_HOSTS", raising=False)
    else:
        monkeypatch.setenv("TRUSTED_API_HOSTS", raw)

    assert trusted_api_hosts() == DEFAULT


def test_configured_list_replaces_the_default(monkeypatch):
    monkeypatch.setenv("TRUSTED_API_HOSTS", "api.cutover.net")

    trusted = trusted_api_hosts()

    check_api_url("https://api.cutover.net", trusted, field="Base-Url")
    with pytest.raises(UntrustedHostError):
        check_api_url("https://api.acme.cutover.com", trusted, field="Base-Url")


@pytest.mark.parametrize(
    "url",
    [
        "https://customer-demo.cutover.com",
        "https://acme.cutover.net",
        "https://your-instance.dev.cutover.cloud",
        "https://your-instance.preview.cutover.dev",
        "https://corp.cutover.com",
        "https://acme.cutover.com/some/path",
    ],
)
def test_core_url_accepts_cutover_instances(url):
    assert check_core_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://evilcutover.com",
        "https://acme.cutover.com.attacker.example",
        "https://x.internal.example.cutover.cloud",
        "https://x.corp.cutover.cloud",
        "http://acme.cutover.com",
        "https://acme.cutover.com:8443",
        "https://10.0.0.1",
        "https://acme.cutover.com?x=1",
        "http://localhost:8000",
    ],
)
def test_core_url_refuses_anything_else(url):
    with pytest.raises(UntrustedHostError, match="Core-Url"):
        check_core_url(url)


@pytest.mark.parametrize(("transport", "expected"), [(None, False), ("stdio", False), ("streamable-http", True)])
def test_enforced_everywhere_except_stdio(monkeypatch, transport, expected):
    if transport is None:
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    else:
        monkeypatch.setenv("MCP_TRANSPORT", transport)

    assert enforced() is expected


def test_enforced_while_serving_an_http_request_without_mcp_transport(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    with patch("fastmcp.server.dependencies.get_http_request", return_value=object()):
        assert enforced() is True
