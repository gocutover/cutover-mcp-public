"""The HTTP app must turn away any /mcp request that has no bearer token, before a session exists."""

import pytest
from starlette.testclient import TestClient

from cutover_mcp.server import mcp

_INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}
_MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


@pytest.fixture
def http_client():
    with TestClient(mcp.http_app(), base_url="http://localhost") as client:
        yield client


@pytest.mark.parametrize(
    "authorization",
    [None, "Basic dXNlcjpwYXNz", "token", "Bearer", "Bearer ", "Bearer    "],
    ids=["none", "basic", "bare-token", "scheme-only", "empty-token", "blank-token"],
)
def test_initialize_without_a_bearer_token_gets_401_and_no_session(http_client, authorization):
    headers = dict(_MCP_HEADERS)
    if authorization is not None:
        headers["Authorization"] = authorization

    response = http_client.post("/mcp", json=_INITIALIZE, headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Bearer")
    assert "mcp-session-id" not in response.headers


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_other_mcp_methods_without_a_bearer_token_get_401(http_client, method):
    response = http_client.request(method, "/mcp", headers={"Mcp-Session-Id": "anything"})

    assert response.status_code == 401


@pytest.mark.parametrize("scheme", ["Bearer", "bearer"])
def test_initialize_with_a_bearer_token_opens_a_session(http_client, scheme):
    response = http_client.post("/mcp", json=_INITIALIZE, headers={**_MCP_HEADERS, "Authorization": f"{scheme} token"})

    assert response.status_code == 200
    assert response.headers["mcp-session-id"]


def test_health_stays_open(http_client):
    response = http_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
