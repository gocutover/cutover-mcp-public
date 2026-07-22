from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import Assignee, TaskLink, TaskResponse, inject_return_schema


@mcp.tool()
@inject_return_schema
async def add_task_to_runbook(
    runbook_id: str,
    name: str,
    description: str = "",
    task_type_id: str | None = None,
    stream_id: str | None = None,
    predecessors: list[str] | None = None,
    duration: int | None = None,
    task_links: list[TaskLink] | None = None,
) -> TaskResponse:
    """
    Add a new task to an existing runbook.

    :param runbook_id: The ID of the runbook to add the task to.
    :param name: The name of the new task.
    :param description: An optional description for the task.
    :param task_type_id: The ID of the task type to associate with this task.
    :param stream_id: The ID of the stream to assign the task to (can be a substream).
    :param predecessors: A list of task IDs that are predecessors to this task.
    :param duration: Planned duration in seconds.
    :param task_links: Links from this task to other resources. Use ``link_type="runbook"`` to link
        a task to a template runbook — the target must be a template and must have ≥1 task, and
        the task's ``task_type_id`` must be the tenant's ``linked`` task type (from
        ``list_task_types``, the entry with ``key == "linked"``) or the link is silently dropped.
        If the parent runbook isn't a template, the response's ``task_links[].id`` references a
        freshly-spawned copy of the template, not the template itself, and the task's name is
        overwritten with the target's name. Use ``link_type="snippet"`` to attach one or more
        snippets.
    :return: A TaskResponse object representing the newly created task.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()
    attributes = {"name": name, "description": description}
    if duration is not None:
        attributes["duration"] = duration
    if task_links is not None:
        attributes["task_links"] = [tl.model_dump() for tl in task_links]

    payload: dict = {"data": {"type": "task", "attributes": attributes}}

    relationships = {}

    if task_type_id is not None:
        relationships["task_type"] = {"data": {"id": task_type_id, "type": "task_type"}}

    if stream_id is not None:
        relationships["stream"] = {"data": {"id": stream_id, "type": "stream"}}

    if predecessors is not None:
        predecessor_data = [{"id": pred_id, "type": "task"} for pred_id in predecessors]
        relationships["predecessors"] = {"data": predecessor_data}

    if relationships:
        payload["data"]["relationships"] = relationships

    response = await client.request("POST", f"core/runbooks/{runbook_id}/tasks", json_data=payload)
    return TaskResponse(**response)


@mcp.tool()
@inject_return_schema
async def update_runbook_task(
    runbook_id: str,
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    predecessors: list[str] | None = None,
    task_type_id: str | None = None,
    stream_id: str | None = None,
    duration: int | None = None,
    custom_field_values: list[dict] | None = None,
    assignees: list[Assignee] | None = None,
    delete_excluded_assignees: bool = False,
    task_links: list[TaskLink] | None = None,
) -> TaskResponse:
    """
    Update an existing task in a runbook (including dependencies, description, stream, duration, etc.).

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to update.
    :param name: The new name for the task.
    :param description: The new description for the task.
    :param predecessors: A list of task IDs that are predecessors to this task.
    :param task_type_id: The ID of the task type to associate with this task.
    :param stream_id: The ID of the stream to assign the task to (can be a substream).
    :param duration: Planned duration in seconds.
    :param custom_field_values: List of custom field values to update. Each item should be a dict with either
        {"name": "Field Name", "value": "value"} or {"custom_field_id": "123", "value": "value"}.
        Value can be a string or list of strings for multi-select fields.
    :param assignees: List of assignees to add to the task. Each item must have an "id" and a "type" of
        either "user" or "runbook_team". Only users and teams that are already participants on the runbook
        can be assigned; non-participants are silently ignored by the API. By default these are added without
        removing existing assignees; set delete_excluded_assignees=True to replace the full list instead.
    :param delete_excluded_assignees: When False (default), adds the given assignees without removing existing
        ones. When True, replaces the full assignee list with only the assignees provided.
    :param task_links: Replaces the task's links to other resources. Use ``link_type="runbook"`` to link
        a task to a template runbook — the target must be a template runbook and must have ≥1 task. Use
        ``link_type="snippet"`` to attach one or more snippets. Pass an empty list to clear all links.
    :return: A TaskResponse object representing the updated task.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```
    """
    client = client_mgr.get_client()
    attributes: dict = {}
    if name is not None:
        attributes["name"] = name
    if description is not None:
        attributes["description"] = description
    if duration is not None:
        attributes["duration"] = duration
    if custom_field_values is not None:
        attributes["custom_field_values"] = custom_field_values
    if task_links is not None:
        attributes["task_links"] = [tl.model_dump() for tl in task_links]

    payload: dict = {"data": {"type": "task", "id": task_id, "attributes": attributes}}

    relationships = {}

    if predecessors is not None:
        predecessor_data = [{"id": pred_id, "type": "task"} for pred_id in predecessors]
        relationships["predecessors"] = {"data": predecessor_data}

    if task_type_id is not None:
        relationships["task_type"] = {"data": {"id": task_type_id, "type": "task_type"}}

    if stream_id is not None:
        relationships["stream"] = {"data": {"id": stream_id, "type": "stream"}}

    if assignees is not None:
        relationships["assignees"] = {"data": [a.model_dump() for a in assignees]}
        payload["meta"] = {"delete_excluded_assignees": delete_excluded_assignees}

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
async def skip_task(runbook_id: str, task_id: str, comment: str) -> dict[str, Any]:
    """
    Skip a specific task in a runbook.

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to skip.
    :param comment: The reason for skipping the task. Required by the API and added as a
        comment on the runbook.
    :return: An acknowledgement dictionary. Unlike start/complete, the skip endpoint does
        not return the task object.
    """
    client = client_mgr.get_client()
    payload = {"meta": {"comment": comment}}
    return await client.request("PATCH", f"core/runbooks/{runbook_id}/tasks/{task_id}/skip", json_data=payload)


@mcp.tool()
async def delete_task(runbook_id: str, task_id: str) -> dict[str, Any]:
    """
    Delete a single task from a runbook.

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to delete.
    :return: An empty dictionary on successful deletion.
    """
    client = client_mgr.get_client()
    return await client.request("DELETE", f"core/runbooks/{runbook_id}/tasks/{task_id}")
