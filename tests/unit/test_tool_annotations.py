import pytest

from cutover_mcp.read_only import ReadOnlyTools
from cutover_mcp.server import mcp

READ_PREFIXES = ("get_", "list_", "query_", "search_")
NOT_READ_ONLY = {"get_data_source_upload_url"}


async def _tools():
    return {tool.name: tool for tool in await mcp.list_tools()}


@pytest.mark.asyncio
async def test_every_tool_sets_all_four_hints():
    tools = await _tools()

    missing = {
        name
        for name, tool in tools.items()
        if tool.annotations is None
        or None
        in (
            tool.annotations.read_only_hint,
            tool.annotations.destructive_hint,
            tool.annotations.idempotent_hint,
            tool.annotations.open_world_hint,
        )
    }

    assert tools
    assert missing == set()


@pytest.mark.asyncio
async def test_read_only_tools_are_the_get_list_query_and_search_tools():
    tools = await _tools()

    read_only = {name for name, tool in tools.items() if tool.annotations.read_only_hint}
    expected = {name for name in tools if name.startswith(READ_PREFIXES)} - NOT_READ_ONLY

    assert read_only == expected


@pytest.mark.asyncio
async def test_read_only_tools_are_not_destructive():
    tools = await _tools()

    assert not [
        name for name, tool in tools.items() if tool.annotations.read_only_hint and tool.annotations.destructive_hint
    ]


@pytest.mark.asyncio
async def test_delete_archive_manage_and_task_lifecycle_tools_are_destructive():
    tools = await _tools()
    prefixes = ("delete_", "archive_", "manage_", "start_", "complete_", "skip_")

    not_destructive = {
        name for name, tool in tools.items() if name.startswith(prefixes) and not tool.annotations.destructive_hint
    }

    assert not_destructive == set()


@pytest.mark.asyncio
async def test_create_add_and_update_tools_are_not_destructive():
    tools = await _tools()

    destructive = {
        name
        for name, tool in tools.items()
        if name.startswith(("create_", "add_", "update_")) and tool.annotations.destructive_hint is not False
    }

    assert destructive == set()


@pytest.mark.asyncio
async def test_open_world_tools_are_the_ones_that_run_integrations_send_comms_or_fetch_a_url():
    tools = await _tools()

    open_world = {name for name, tool in tools.items() if tool.annotations.open_world_hint}

    assert open_world == {"manage_data_source", "manage_runbook", "start_task", "complete_task", "skip_task"}


@pytest.mark.asyncio
async def test_read_only_transform_keeps_only_the_read_only_tools():
    tools = await _tools()

    kept = {tool.name for tool in await ReadOnlyTools().list_tools(list(tools.values()))}

    assert kept == {name for name in tools if name.startswith(READ_PREFIXES)} - NOT_READ_ONLY
    assert "delete_task" not in kept
