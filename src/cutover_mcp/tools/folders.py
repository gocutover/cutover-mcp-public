from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import FolderListResponse, inject_return_schema


@mcp.tool()
@inject_return_schema
async def list_folders(workspace_id: str) -> FolderListResponse:
    """
    List all folders in a specific workspace.

    :param workspace_id: The unique identifier for the workspace.
    :return: A FolderListResponse object containing a list of folders.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()

    path: str | None = f"core/workspaces/{workspace_id}/folders"
    all_data: list[dict[str, Any]] = []
    last_response: dict[str, Any] = {}

    while path:
        response = await client.request("GET", path)
        all_data.extend(response.get("data", []))
        last_response = response
        path = response.get("links", {}).get("next")

    return FolderListResponse(
        **{
            "data": all_data,
            "meta": last_response.get("meta", {"page": {"number": 1, "total": len(all_data)}}),
            "links": last_response.get("links", {"self": f"core/workspaces/{workspace_id}/folders"}),
        }
    )
