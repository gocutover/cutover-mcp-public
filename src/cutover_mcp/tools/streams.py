from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import StreamListResponse, StreamResponse, inject_return_schema


@mcp.tool()
@inject_return_schema
async def list_streams(runbook_id: str, forecast: bool = False) -> StreamListResponse:
    """
    List all streams for a specific runbook, including substreams.

    :param runbook_id: The ID of the runbook to list streams for.
    :param forecast: If true, returns computed forecast fields (start_display, end_display, etc.).
    :return: A StreamListResponse object containing a list of streams.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()
    params = {"forecast": "true"} if forecast else {}
    response = await client.request("GET", f"core/runbooks/{runbook_id}/streams", params=params)
    return StreamListResponse(**response)


@mcp.tool()
@inject_return_schema
async def create_stream(
    runbook_id: str,
    name: str,
    description: str = "",
    color: str | None = None,
    parent_stream_id: str | None = None,
) -> StreamResponse:
    """
    Create a new stream or substream in a runbook.

    :param runbook_id: The ID of the runbook to create the stream in.
    :param name: The name of the new stream.
    :param description: An optional description for the stream.
    :param color: The color assigned to the stream in CSS-friendly format (e.g., "#f0f0f0" or "rgb(0,0,0)").
    :param parent_stream_id: The ID of the parent stream if creating a substream.
    :return: A StreamResponse object representing the newly created stream.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()
    attributes = {"name": name}
    if description:
        attributes["description"] = description
    if color:
        attributes["color"] = color

    payload = {"data": {"type": "stream", "attributes": attributes}}

    if parent_stream_id is not None:
        payload["data"]["relationships"] = {"parent": {"data": {"id": parent_stream_id, "type": "stream"}}}

    response = await client.request("POST", f"core/runbooks/{runbook_id}/streams", json_data=payload)
    return StreamResponse(**response)


@mcp.tool()
@inject_return_schema
async def get_stream(runbook_id: str, stream_id: str) -> StreamResponse:
    """
    Get details of a specific stream or substream in a runbook.

    :param runbook_id: The ID of the runbook containing the stream.
    :param stream_id: The ID of the stream to retrieve.
    :return: A StreamResponse object representing the stream.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()
    response = await client.request("GET", f"core/runbooks/{runbook_id}/streams/{stream_id}")
    return StreamResponse(**response)


@mcp.tool()
@inject_return_schema
async def update_stream(
    runbook_id: str,
    stream_id: str,
    name: str | None = None,
    description: str | None = None,
    color: str | None = None,
) -> StreamResponse:
    """
    Update an existing stream in a runbook.

    :param runbook_id: The ID of the runbook containing the stream.
    :param stream_id: The ID of the stream to update.
    :param name: The new name for the stream.
    :param description: The new description for the stream.
    :param color: The new color for the stream in CSS-friendly format.
    :return: A StreamResponse object representing the updated stream.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()
    attributes = {}
    if name is not None:
        attributes["name"] = name
    if description is not None:
        attributes["description"] = description
    if color is not None:
        attributes["color"] = color

    payload = {"data": {"type": "stream", "id": stream_id, "attributes": attributes}}

    response = await client.request("PATCH", f"core/runbooks/{runbook_id}/streams/{stream_id}", json_data=payload)
    return StreamResponse(**response)


@mcp.tool()
async def delete_stream(runbook_id: str, stream_id: str) -> dict[str, Any]:
    """
    Delete a stream from a runbook.

    :param runbook_id: The ID of the runbook containing the stream.
    :param stream_id: The ID of the stream to delete.
    :return: An empty dictionary on successful deletion.
    """
    client = client_mgr.get_client()
    return await client.request("DELETE", f"core/runbooks/{runbook_id}/streams/{stream_id}")
