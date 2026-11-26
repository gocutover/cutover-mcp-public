import os
from collections.abc import Sequence

from fastmcp.server.transforms import GetToolNext, Transform
from fastmcp.tools import Tool
from fastmcp.utilities.versions import VersionSpec

_TRUE = {"true", "1", "yes"}
_FALSE = {"", "false", "0", "no"}


def read_only_mode() -> bool:
    """Whether MCP_READ_ONLY asks for only the read-only tools. An unrecognised value raises
    rather than falling back to exposing write tools."""
    value = os.getenv("MCP_READ_ONLY", "").strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ValueError(f"MCP_READ_ONLY must be true or false, not {os.getenv('MCP_READ_ONLY')!r}.")


def is_read_only(tool: Tool) -> bool:
    return tool.annotations is not None and tool.annotations.read_only_hint is True


class ReadOnlyTools(Transform):
    """Hides every tool not annotated read-only, from listing and from calls."""

    async def list_tools(self, tools: Sequence[Tool]) -> Sequence[Tool]:
        return [tool for tool in tools if is_read_only(tool)]

    async def get_tool(self, name: str, call_next: GetToolNext, *, version: VersionSpec | None = None) -> Tool | None:
        tool = await call_next(name, version=version)
        return tool if tool is not None and is_read_only(tool) else None
