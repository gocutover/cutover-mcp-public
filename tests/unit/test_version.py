import httpx
import pytest

from cutover_mcp import __version__
from cutover_mcp.app import mcp
from cutover_mcp.clients.api import APIClient


def test_version_comes_from_package_metadata():
    """The version is derived from the git tag by hatch-vcs and read back from the installed metadata."""
    assert isinstance(__version__, str)
    assert __version__  # "0.0.0" when no metadata is available, never empty
    assert mcp.version == __version__


@pytest.mark.asyncio
async def test_health_reports_version_and_sha(monkeypatch):
    monkeypatch.setenv("CUTOVER_MCP_GIT_SHA", "abc1234")

    transport = httpx.ASGITransport(app=mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "sha": "abc1234"}


@pytest.mark.asyncio
async def test_health_sha_is_null_outside_docker(monkeypatch):
    monkeypatch.delenv("CUTOVER_MCP_GIT_SHA", raising=False)

    transport = httpx.ASGITransport(app=mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.json()["sha"] is None


@pytest.mark.asyncio
async def test_user_agent_carries_the_package_version():
    api = APIClient("https://api.example.com", "token")
    try:
        client = await api._get_client()
        assert client.headers["User-Agent"] == f"CutoverMCP/{__version__}"
    finally:
        await api.aclose()
