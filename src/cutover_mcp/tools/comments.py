from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import CommentResponse, inject_return_schema


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
    client = client_mgr.get_client()
    payload: dict = {"data": {"type": "comment", "attributes": {"content": content}}}

    if task_id is not None:
        payload["data"]["relationships"] = {"task": {"data": {"id": task_id, "type": "task"}}}

    response = await client.request("POST", f"core/runbooks/{runbook_id}/comments", json_data=payload)
    return CommentResponse(**response)
