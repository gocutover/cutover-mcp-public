from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def list_task_types() -> dict[str, Any]:
    """
    List all task types.

    :return: A dictionary containing a list of task types.
    """
    client = client_mgr.get_client()
    return await client.request("GET", "core/task_types")
