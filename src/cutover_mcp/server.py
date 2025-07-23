# server.py (Main FastMCP server definition)
import logging

from dotenv import load_dotenv

# Import the central mcp object from our new app.py file
from cutover_mcp.app import mcp

# Import modules to register their components. This is the magic step.
# Because these modules also import `mcp` from `app.py`, their decorators
# will register tools and resources on the correct central instance.
from cutover_mcp.tools import action_log, runbooks, streams, task_types, tasks, workspaces  # noqa: F401

# Load environment variables from .env file first
load_dotenv()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    mcp.run()
