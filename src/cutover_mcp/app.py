# src/cutover_mcp/app.py
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from cutover_mcp.clients.api import APIClientManager
import logging


from dotenv import load_dotenv

# This is the central server instance that all other modules will import
# to register their tools and resources.
load_dotenv()

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="Cutover MCP Server",
    instructions="A set of tools and resources for interacting with the Cutover platform."
)

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manages the application lifecycle (startup and shutdown)."""
    logger.info("Server starting up...")
    client_manager = APIClientManager()
    server.state.client_manager = client_manager
    yield
    logger.info("Server shutting down...")
    await client_manager.close_all()

# Attach the lifespan manager to our imported mcp object
mcp.lifespan = app_lifespan
