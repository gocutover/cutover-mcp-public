# src/cutover_mcp/app.py
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from cutover_mcp import __version__
from cutover_mcp.clients.api import client_mgr

# This is the central server instance that all other modules will import
# to register their tools and resources.
load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manages the application lifecycle (startup and shutdown)."""
    logger.info("Server starting up (cutover-mcp %s)...", __version__)
    yield
    logger.info("Server shutting down...")
    await client_mgr.close_all()


mcp = FastMCP(
    name="Cutover MCP Server",
    version=__version__,
    instructions="A set of tools and resources for interacting with the Cutover platform.",
    lifespan=app_lifespan,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    # CUTOVER_MCP_GIT_SHA is baked into the Docker image by build.yml; absent for local runs.
    return JSONResponse(
        {
            "status": "ok",
            "version": __version__,
            "sha": os.getenv("CUTOVER_MCP_GIT_SHA") or None,
        }
    )
