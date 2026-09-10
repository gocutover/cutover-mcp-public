"""Cutover MCP server package."""

from importlib.metadata import PackageNotFoundError, version

try:
    # The installed package metadata is derived from the git tag by hatch-vcs (see pyproject.toml),
    # so this is the single place the code learns its own version.
    __version__ = version("cutover-mcp")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0.0.0"
