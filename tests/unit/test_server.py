"""The HTTP server keeps no per-session state, so any replica can serve any request."""

from unittest.mock import patch

import httpx
import pytest

from cutover_mcp import server
from cutover_mcp.app import mcp

_HEADERS = {
    "content-type": "application/json",
    "accept": "application/json, text/event-stream",
    "authorization": "Bearer test-token",
}
_INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
}
_LIST_TOOLS = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}


async def _send(method: str, body: dict | None = None) -> httpx.Response:
    """Send one request to a fresh app instance, standing in for a replica that has seen nothing else."""
    app = mcp.http_app(stateless_http=True)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://replica") as client,
    ):
        return await client.request(method, "/mcp", json=body, headers=_HEADERS)


def _run_kwargs(monkeypatch, transport: str) -> dict:
    monkeypatch.setenv("MCP_TRANSPORT", transport)
    with patch.object(server.mcp, "run") as run:
        server.main()
    return run.call_args.kwargs


def test_streamable_http_runs_stateless(monkeypatch):
    assert _run_kwargs(monkeypatch, "streamable-http")["stateless_http"] is True


def test_sse_keeps_sessions_because_it_cannot_run_stateless(monkeypatch):
    assert _run_kwargs(monkeypatch, "sse")["stateless_http"] is False


def test_stdio_takes_no_http_options():
    with patch.object(server.mcp, "run") as run:
        server.main()
    run.assert_called_once_with()


@pytest.mark.asyncio
async def test_a_call_lands_on_a_replica_that_never_saw_initialize():
    first = await _send("POST", _INITIALIZE)
    assert first.status_code == 200
    assert "mcp-session-id" not in first.headers

    second = await _send("POST", _LIST_TOOLS)
    assert second.status_code == 200
    assert '"tools"' in second.text


@pytest.mark.asyncio
async def test_stateless_server_offers_no_get_stream():
    assert (await _send("GET")).status_code == 405
