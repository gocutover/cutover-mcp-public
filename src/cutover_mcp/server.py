# server.py (Main FastMCP server definition)
import logging
import os
import sys

from dotenv import load_dotenv

# Import the central mcp object from our new app.py file
from cutover_mcp.app import mcp

# Import modules to register their components. This is the magic step.
# Because these modules also import `mcp` from `app.py`, their decorators
# will register tools and resources on the correct central instance.
from cutover_mcp.tools import (  # noqa: F401
    action_log,
    activities,
    comments,
    custom_fields,
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

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(
            transport=transport,
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8000")),
        )
