from typing import List, Dict, Any, Optional

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def add_task_to_runbook(runbook_id: str, name: str, description: str = "") -> dict:
    """
    Add a new task to an existing runbook.

    :param runbook_id: The ID of the runbook to add the task to.
    :param name: The name of the new task.
    :param description: An optional description for the task.
    :return: A dictionary representing the newly created task.
    """
    client = client_mgr.get_client()
    payload = {
        "data": {"type": "task", "attributes": {"name": name, "description": description}}
    }
    return await client.request("POST", f"core/runbooks/{runbook_id}/tasks", json_data=payload)


@mcp.tool()
async def update_runbook_task(
    runbook_id: str,
    task_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    predecessors: Optional[List[str]] = None,
) -> dict:
    """
    Update an existing task in a runbook (including dependencies, description, etc.).

    :param runbook_id: The ID of the runbook containing the task.
    :param task_id: The ID of the task to update.
    :param name: The new name for the task.
    :param description: The new description for the task.
    :param predecessors: A list of task IDs that are predecessors to this task.
    :return: A dictionary representing the updated task.
    """
    client = client_mgr.get_client()
    attributes = {}
    if name is not None:
        attributes["name"] = name
    if description is not None:
        attributes["description"] = description

    payload = {"data": {"type": "task", "id": task_id, "attributes": attributes}}

    if predecessors is not None:
        predecessor_data = [
            {"id": pred_id, "type": "task"} for pred_id in predecessors
        ]
        payload["data"]["relationships"] = {"predecessors": {"data": predecessor_data}}

    return await client.request(
        "PATCH", f"core/runbooks/{runbook_id}/tasks/{task_id}", json_data=payload
    )