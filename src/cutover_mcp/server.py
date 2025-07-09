# server.py (Main FastMCP server definition)
import logging

from dotenv import load_dotenv

# Import the central mcp object from our new app.py file
from cutover_mcp.app import mcp

# Load environment variables from .env file first
load_dotenv()

logger = logging.getLogger(__name__)


# Import modules to register their components. This is the magic step.
# Because these modules also import `mcp` from `app.py`, their decorators
# will register tools and resources on the correct central instance.


@mcp.resource("cutover://")
async def root() -> dict:
    """
    Root resource for the Cutover MCP server.
    Returns a simple message indicating the server is running.
    """
    return {"message": "Welcome to the Cutover MCP Server!"}


@mcp.tool()
async def ping() -> dict:
    """
    A simple tool to check if the server is running.
    Returns a message indicating the server is alive.
    """
    return {"message": "Cutover MCP Server is running!"}


if __name__ == "__main__":
    mcp.run()
