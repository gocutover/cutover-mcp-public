from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import RunbookListResponse, RunbookResponse, TaskListResponse, inject_return_schema


@mcp.tool()
@inject_return_schema
async def get_runbook_by_id(runbook_id: str) -> RunbookResponse:
    """
    Fetch details for a specific runbook by its ID.

    :param runbook_id: The unique identifier for the runbook.
    :return: A RunbookResponse object containing the runbook details.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```
    """
    client = client_mgr.get_client()
    response = await client.request("GET", f"core/runbooks/{runbook_id}")
    return RunbookResponse(**response)


@mcp.tool()
async def list_runbooks(workspace_id: str) -> RunbookListResponse:
    """
    List all runbooks in a specific workspace.

    :param workspace_id: The unique identifier for the workspace.
    :return: A RunbookListResponse object containing a list of runbooks.
    """
    client = client_mgr.get_client()
    params = {"workspace_id": workspace_id}
    response = await client.request("GET", "core/runbooks", params=params)
    return RunbookListResponse(**response)


@mcp.tool()
async def get_runbook_tasks(runbook_id: str) -> TaskListResponse:
    """
    Fetch all tasks for a specific runbook.

    :param runbook_id: The unique identifier for the runbook.
    :return: A TaskListResponse object containing a list of tasks for the specified runbook.
    """
    client = client_mgr.get_client()
    response = await client.request("GET", f"core/runbooks/{runbook_id}/tasks")
    return TaskListResponse(**response)


@mcp.tool()
async def create_runbook(workspace_id: str, name: str, description: str = "") -> RunbookResponse:
    """
    Create a new runbook in a workspace.

    :param workspace_id: The ID of the workspace to create the runbook in.
    :param name: The name of the new runbook.
    :param description: An optional description for the runbook.
    :return: A RunbookResponse object representing the newly created runbook.
    """
    client = client_mgr.get_client()
    payload = {
        "data": {
            "type": "runbook",
            "attributes": {"name": name, "description": description},
            "relationships": {"workspace": {"data": {"type": "workspace", "id": workspace_id}}},
        }
    }
    response = await client.request("POST", "core/runbooks", json_data=payload)
    return RunbookResponse(**response)


@mcp.tool()
async def manage_runbook(
    runbook_id: str,
    action: str,
    comms: str | None = None,
    disable_task_notify: bool | None = False,
    run_type: str | None = None,
    rebaseline: bool | None = False,
    shift_fixed_times: bool | None = False,
    validation_level: str | None = "error",
    message: str | None = None,
    notify: bool | None = False,
) -> dict[str, Any]:
    """
    Manage a specific runbook by performing an action (start, cancel, pause, resume). These are the only possible actions with this tool.

    :param runbook_id: The unique identifier for the runbook.
    :param action: The action to perform (start, cancel, pause, resume).
    :param comms: Communication mode (off, test, on) (for start).
    :param disable_task_notify: Disable task start notifications (for start).
    :param run_type: Type of run (live, rehearsal) (for start).
    :param rebaseline: Recalculate all planned times based on the current time (for start).
    :param shift_fixed_times: Shift tasks with fixed times relative to the current time (for start).
    :param validation_level: Validation level (warning, error) (for start).
    :param message: Optional message (for cancel, pause, resume).
    :param notify: Notify users about the action (for cancel, pause, resume).
    :return: A dictionary containing the response from the server.
    """
    client = client_mgr.get_client()

    # Define the endpoint based on the action
    endpoint_map = {
        "start": f"core/runbooks/{runbook_id}/start",
        "cancel": f"core/runbooks/{runbook_id}/cancel",
        "pause": f"core/runbooks/{runbook_id}/pause",
        "resume": f"core/runbooks/{runbook_id}/resume",
    }

    if action not in endpoint_map:
        raise ValueError(f"Invalid action: {action}. Must be one of {list(endpoint_map.keys())}.")

    endpoint = endpoint_map[action]

    # Prepare the payload based on the action
    if action == "start":
        payload = {
            "meta": {
                "comms": comms,
                "disable_task_notify": disable_task_notify,
                "run_type": run_type,
                "rebaseline": rebaseline,
                "shift_fixed_times": shift_fixed_times,
                "validation_level": validation_level,
            }
        }
    else:
        payload = {
            "meta": {
                "message": message,
                "notify": notify,
            }
        }

    # Remove keys with None values to avoid sending unnecessary fields
    if "meta" in payload:
        payload["meta"] = {k: v for k, v in payload["meta"].items() if v is not None}

    return await client.request("PATCH", endpoint, json_data=payload)
