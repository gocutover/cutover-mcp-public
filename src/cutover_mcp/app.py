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
from cutover_mcp.read_only import ReadOnlyTools, read_only_mode
from cutover_mcp.security import host_policy
from cutover_mcp.security.bearer import RequireBearerToken

# This is the central server instance that all other modules will import
# to register their tools and resources.
load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manages the application lifecycle (startup and shutdown)."""
    logger.info("Server starting up (cutover-mcp %s)...", __version__)
    # Every entry point runs this lifespan (server.py, `fastmcp run`, mcp.http_app()), so a
    # malformed TRUSTED_API_HOSTS stops each of them before any traffic is served.
    host_policy.trusted_api_hosts()
    if read_only_mode():
        logger.info("MCP_READ_ONLY is set: only read-only tools are available.")
    yield
    logger.info("Server shutting down...")
    await client_mgr.close_all()


mcp = FastMCP(
    name="Cutover MCP Server",
    version=__version__,
    instructions="A set of tools and resources for interacting with the Cutover platform.",
    lifespan=app_lifespan,
    transforms=[ReadOnlyTools()] if read_only_mode() else [],
    # Over HTTP, /mcp needs an Authorization: Bearer header; stdio is not affected.
    auth=RequireBearerToken(),
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
