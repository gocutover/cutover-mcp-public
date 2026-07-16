# src/cutover_mcp/app.py
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastmcp import FastMCP

from cutover_mcp.clients.api import client_mgr

# This is the central server instance that all other modules will import
# to register their tools and resources.
load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manages the application lifecycle (startup and shutdown)."""
    logger.info("Server starting up...")
    yield
    logger.info("Server shutting down...")
    await client_mgr.close_all()


mcp = FastMCP(
    name="Cutover MCP Server",
    instructions="A set of tools and resources for interacting with the Cutover platform.",
    lifespan=app_lifespan,
)
