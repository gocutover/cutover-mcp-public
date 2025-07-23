from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import TaskResponse, inject_return_schema


@mcp.tool()
@inject_return_schema
async def add_task_to_runbook(
    runbook_id: str, name: str, description: str = "", task_type_id: str | None = None, stream_id: str | None = None
) -> TaskResponse:
    """
    Add a new task to an existing runbook.

    :param runbook_id: The ID of the runbook to add the task to.
    :param name: The name of the new task.
    :param description: An optional description for the task.
    :param task_type_id: The ID of the task type to associate with this task.
    :param stream_id: The ID of the stream to assign the task to (can be a substream).
    :return: A TaskResponse object representing the newly created task.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()
    payload = {"data": {"type": "task", "attributes": {"name": name, "description": description}}}

    relationships = {}

    if task_type_id is not None:
        relationships["task_type"] = {"data": {"id": task_type_id, "type": "task_type"}}

    if stream_id is not None:
        relationships["stream"] = {"data": {"id": stream_id, "type": "stream"}}

    if relationships:
        payload["data"]["relationships"] = relationships

    response = await client.request("POST", f"core/runbooks/{runbook_id}/tasks", json_data=payload)
    return TaskResponse(**response)


@mcp.tool()
async def update_runbook_task(
    runbook_id: str,
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    predecessors: list[str] | None = None,
    task_type_id: str | None = None,
    stream_id: str | None = None,
) -> TaskResponse:
    """
    Update an existing task in a runbook (including dependencies, description, stream, etc.).

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to update.
    :param name: The new name for the task.
    :param description: The new description for the task.
    :param predecessors: A list of task IDs that are predecessors to this task.
    :param task_type_id: The ID of the task type to associate with this task.
    :param stream_id: The ID of the stream to assign the task to (can be a substream).
    :return: A TaskResponse object representing the updated task.
    """
    client = client_mgr.get_client()
    attributes = {}
    if name is not None:
        attributes["name"] = name
    if description is not None:
        attributes["description"] = description

    payload = {"data": {"type": "task", "id": task_id, "attributes": attributes}}

    relationships = {}

    if predecessors is not None:
        predecessor_data = [{"id": pred_id, "type": "task"} for pred_id in predecessors]
        relationships["predecessors"] = {"data": predecessor_data}

    if task_type_id is not None:
        relationships["task_type"] = {"data": {"id": task_type_id, "type": "task_type"}}

    if stream_id is not None:
        relationships["stream"] = {"data": {"id": stream_id, "type": "stream"}}

    if relationships:
        payload["data"]["relationships"] = relationships

    response = await client.request("PATCH", f"core/runbooks/{runbook_id}/tasks/{task_id}", json_data=payload)
    return TaskResponse(**response)


@mcp.tool()
async def start_task(runbook_id: str, task_id: str) -> TaskResponse:
    """
    Start a specific task in a runbook.

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to start.
    :return: A TaskResponse object representing the started task.
    """
    client = client_mgr.get_client()
    response = await client.request("PATCH", f"core/runbooks/{runbook_id}/tasks/{task_id}/start")
    return TaskResponse(**response)


@mcp.tool()
async def complete_task(runbook_id: str, task_id: str) -> TaskResponse:
    """
    Complete a specific task in a runbook.

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to complete.
    :return: A TaskResponse object representing the completed task.
    """
    client = client_mgr.get_client()
    response = await client.request("PATCH", f"core/runbooks/{runbook_id}/tasks/{task_id}/finish")
    return TaskResponse(**response)


@mcp.tool()
async def skip_task(runbook_id: str, task_id: str) -> TaskResponse:
    """
    Skip a specific task in a runbook.

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to skip.
    :return: A TaskResponse object representing the skipped task.
    """
    client = client_mgr.get_client()
    response = await client.request("PATCH", f"core/runbooks/{runbook_id}/tasks/{task_id}/skip")
    return TaskResponse(**response)
