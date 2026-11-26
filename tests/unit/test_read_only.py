import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from cutover_mcp.read_only import ReadOnlyTools, read_only_mode
from cutover_mcp.tools.annotations import READ_ONLY, writes


def _server(*, read_only: bool) -> FastMCP:
    server = FastMCP("test", transforms=[ReadOnlyTools()] if read_only else [])

    @server.tool(annotations=READ_ONLY)
    def read_thing() -> str:
        return "read"

    @server.tool(annotations=writes(destructive=True, idempotent=True))
    def delete_thing() -> str:
        return "deleted"

    @server.tool()
    def unannotated_thing() -> str:
        return "unannotated"

    return server


@pytest.mark.asyncio
async def test_read_only_server_lists_only_read_only_tools():
    async with Client(_server(read_only=True)) as client:
        names = {tool.name for tool in await client.list_tools()}

    assert names == {"read_thing"}


@pytest.mark.asyncio
async def test_read_only_server_refuses_to_call_a_write_tool():
    async with Client(_server(read_only=True)) as client:
        with pytest.raises(ToolError, match="delete_thing"):
            await client.call_tool("delete_thing")


@pytest.mark.asyncio
async def test_read_only_server_refuses_to_call_an_unannotated_tool():
    async with Client(_server(read_only=True)) as client:
        with pytest.raises(ToolError, match="unannotated_thing"):
            await client.call_tool("unannotated_thing")


@pytest.mark.asyncio
async def test_read_only_server_calls_a_read_only_tool():
    async with Client(_server(read_only=True)) as client:
        result = await client.call_tool("read_thing")

    assert result.data == "read"


@pytest.mark.asyncio
async def test_server_without_the_transform_lists_every_tool():
    async with Client(_server(read_only=False)) as client:
        names = {tool.name for tool in await client.list_tools()}

    assert names == {"read_thing", "delete_thing", "unannotated_thing"}


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", " true "])
def test_read_only_mode_is_on_for_true_values(monkeypatch, value):
    monkeypatch.setenv("MCP_READ_ONLY", value)

    assert read_only_mode() is True


@pytest.mark.parametrize("value", ["", "false", "0", "no"])
def test_read_only_mode_is_off_for_false_values(monkeypatch, value):
    monkeypatch.setenv("MCP_READ_ONLY", value)

    assert read_only_mode() is False


def test_read_only_mode_is_off_when_unset(monkeypatch):
    monkeypatch.delenv("MCP_READ_ONLY", raising=False)

    assert read_only_mode() is False


def test_read_only_mode_rejects_an_unrecognised_value(monkeypatch):
    monkeypatch.setenv("MCP_READ_ONLY", "ture")

    with pytest.raises(ValueError, match="MCP_READ_ONLY"):
        read_only_mode()
