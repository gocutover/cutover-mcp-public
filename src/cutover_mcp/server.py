# server.py (Main FastMCP server definition)
import logging
import os
import sys

from dotenv import load_dotenv

# Import the central mcp object from our new app.py file
from cutover_mcp.app import mcp
from cutover_mcp.security import host_policy

# Import modules to register their components. This is the magic step.
# Because these modules also import `mcp` from `app.py`, their decorators
# will register tools and resources on the correct central instance.
from cutover_mcp.tools import (  # noqa: F401
    action_log,
    activities,
    comments,
    custom_fields,
    data_sources,
    folders,
    runbook_types,
    runbooks,
    streams,
    task_types,
    tasks,
    teams,
    users,
    workspaces,
)

# Load environment variables from .env file first
load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the server. This is the `cutover-mcp` console script (see [project.scripts] in pyproject.toml),
    so `uvx cutover-mcp`, `uv run cutover-mcp` and `python src/cutover_mcp/server.py` all land here."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "stdio":
        mcp.run()
    else:
        trusted = host_policy.trusted_api_hosts()
        logger.info("Trusted API hosts: %s", ", ".join(sorted(".".join(p.labels) for p in trusted)))
        mcp.run(
            transport=transport,
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8000")),
        )


if __name__ == "__main__":
    main()
