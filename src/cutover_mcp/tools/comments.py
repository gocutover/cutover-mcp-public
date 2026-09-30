from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import CommentListResponse, CommentResponse, inject_return_schema


@mcp.tool()
@inject_return_schema
async def add_comment(
    runbook_id: str,
    content: str,
    task_id: str | None = None,
) -> CommentResponse:
    """
    Post a comment on a runbook, optionally attached to a specific task.

    Use this to record progress notes or results (e.g. while working through a runbook's
    tasks) without overwriting task descriptions.

    :param runbook_id: The ID of the runbook to comment on.
    :param content: The text content of the comment. Content supports a limited set of HTML tags (for example, <p>, <b>, <ul>, <code>); markdown is not rendered and disallowed tags are stripped.
    :param task_id: Optional ID of the task to attach the comment to (the same task ID used
        by the other task tools). When omitted, the comment is posted at runbook level.
    :return: A CommentResponse object representing the newly created comment.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = await client_mgr.get_client()
    payload: dict = {"data": {"type": "comment", "attributes": {"content": content}}}

    if task_id is not None:
        payload["data"]["relationships"] = {"task": {"data": {"id": task_id, "type": "task"}}}

    response = await client.request("POST", f"core/runbooks/{runbook_id}/comments", json_data=payload)
    return CommentResponse(**response)


@mcp.tool()
@inject_return_schema
async def get_comments(
    runbook_id: str,
    task_id: str | None = None,
) -> CommentListResponse:
    """
    List the comments on a runbook, optionally filtered to a specific task.

    Comments are the append-only, timestamped log channel while a runbook is running (task
    descriptions are locked outside edit/dynamic mode), so this is how to read back progress
    notes or status that were recorded earlier with add_comment, by a person or by an agent.

    :param runbook_id: The ID of the runbook to read comments from.
    :param task_id: Optional ID of a task (the same task ID used by the other task tools) to
        return only the comments attached to that task. When omitted, every comment on the
        runbook is returned, including runbook-level ones.
    :return: A CommentListResponse object containing a list of comments (all pages are fetched
        and aggregated).

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = await client_mgr.get_client()

    path: str | None = f"core/runbooks/{runbook_id}/comments"
    params: dict | None = {"task_id": task_id} if task_id is not None else {}
    all_data: list[dict[str, Any]] = []
    last_response: dict[str, Any] = {}

    # params passed on first request; subsequent requests follow links.next verbatim
    while path:
        response = await client.request("GET", path, params=params)
        params = None
        all_data.extend(response.get("data", []))
        last_response = response
        path = response.get("links", {}).get("next")

    return CommentListResponse(
        **{
            "data": all_data,
            "meta": last_response.get("meta", {"page": {"number": 1, "total": len(all_data)}}),
            "links": last_response.get("links", {"self": f"core/runbooks/{runbook_id}/comments"}),
        }
    )
