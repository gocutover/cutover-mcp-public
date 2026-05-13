from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import RunbookTypeListResponse, inject_return_schema


@mcp.tool()
@inject_return_schema
async def list_runbook_types() -> RunbookTypeListResponse:
    """
    List all runbook types in the instance.

    :return: A RunbookTypeListResponse object containing a list of runbook types.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```
    """
    client = client_mgr.get_client()
    all_data = []
    path: str | None = "core/runbook_types"
    last_response: dict = {}

    while path:
        response = await client.request("GET", path)
        all_data.extend(response.get("data", []))
        last_response = response
        path = response.get("links", {}).get("next")

    return RunbookTypeListResponse(
        **{
            "data": all_data,
            "included": last_response.get("included", []),
            "meta": last_response.get("meta", {"page": {"number": 1, "total": len(all_data)}}),
            "links": last_response.get("links", {"self": "core/runbook_types"}),
        }
    )
