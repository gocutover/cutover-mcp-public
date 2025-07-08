from typing import Optional, Dict, Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def get_workspace_by_id(workspace_id: str) -> Dict[str, Any]:
    """
    Fetch details for a specific workspace by its ID.

    :param workspace_id: The unique identifier for the workspace.
    :return: A dictionary containing the workspace details.
    """
    client = client_mgr.get_client()
    return await client.request("GET", f"core/workspaces/{workspace_id}")


@mcp.tool()
async def query_workspaces(query: str) -> Dict[str, Any]:
    """
    Search for workspaces by name or query string.

    :param query: The search string to filter workspaces by.
    :return: A dictionary containing a list of workspaces matching the query.
    """
    client = client_mgr.get_client()
    params = {"query": query}
    return await client.request("GET", "core/workspaces", params=params)


@mcp.tool()
async def list_workspaces(limit: int = 50, offset: int = 0) -> dict:
    """
    List all workspaces.

    :param limit: The maximum number of workspaces to return.
    :param offset: The number of workspaces to skip from the beginning.
    :return: A dictionary containing a list of workspaces.
    """
    client = client_mgr.get_client()
    params = {"page[limit]": limit, "page[offset]": offset}
    return await client.request("GET", "core/workspaces", params=params)


@mcp.tool()
async def create_workspace(name: str, description: str = "", key: str = "") -> dict:
    """
    Create a new account/workspace.

    :param name: The name of the new workspace/account.
    :param description: An optional description for the workspace/account.
    :param key: Required, shortened version of the workspace/account name.
    :return: A dictionary representing the newly created workspace/account.
    """
    client = client_mgr.get_client()
    payload = {
        "data": {
            "type": "workspace",
            "attributes": { "name": name, "description": description, "key": key }
        }
    }
    
    return await client.request("POST", "core/workspaces", json_data=payload)
