from typing import Optional, Dict, Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def get_runbook_by_id(runbook_id: str) -> Dict[str, Any]:
    """
    Fetch details for a specific runbook by its ID.

    :param runbook_id: The unique identifier for the runbook.
    :return: A dictionary containing the runbook details.
    """
    client = client_mgr.get_client()
    return await client.request("GET", f"core/runbooks/{runbook_id}")


@mcp.tool()
async def list_runbooks(workspace_id: str) -> Dict[str, Any]:
    """
    List all runbooks in a specific workspace.

    :param workspace_id: The unique identifier for the workspace.
    :return: A dictionary containing a list of runbooks.
    """
    client = client_mgr.get_client()
    params = {"workspace_id": workspace_id}
    return await client.request("GET", "core/runbooks", params=params)


@mcp.tool()
async def get_runbook_tasks(runbook_id: str) -> Dict[str, Any]:
    """
    Fetch all tasks for a specific runbook.

    :param runbook_id: The unique identifier for the runbook.
    :return: A dictionary containing a list of tasks for the specified runbook.
    """
    client = client_mgr.get_client()
    return await client.request("GET", f"core/runbooks/{runbook_id}/tasks")


@mcp.tool()
async def create_runbook(workspace_id: str, name: str, description: str = "") -> dict:
    """
    Create a new runbook in a workspace.

    :param workspace_id: The ID of the workspace to create the runbook in.
    :param name: The name of the new runbook.
    :param description: An optional description for the runbook.
    :return: A dictionary representing the newly created runbook.
    """
    client = client_mgr.get_client()
    payload = {
        "data": {
            "type": "runbook",
            "attributes": {"name": name, "description": description},
            "relationships": {
                "workspace": {"data": {"type": "workspace", "id": workspace_id}}
            },
        }
    }
    return await client.request("POST", "core/runbooks", json_data=payload)