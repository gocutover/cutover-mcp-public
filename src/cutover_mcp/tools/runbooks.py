from typing import Any, Literal
from urllib.parse import urlencode

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
async def list_runbooks(
    workspace_id: str,
    is_template: bool | None = None,
    archived: bool | None = None,
    source_runbook_id: str | None = None,
    folder_id: str | None = None,
    extra_params: dict[str, Any] | None = None,
) -> RunbookListResponse:
    """
    List all runbooks in a specific workspace.

    :param workspace_id: The unique identifier for the workspace.
    :param is_template: Filter by template status. Pass false to exclude templates, true to show only templates.
    :param archived: Filter by archived status. Pass false to exclude archived runbooks, true to show only archived.
    :param source_runbook_id: Filter to only runbooks created from this template ID.
    :param folder_id: Filter to only runbooks in this folder ID.
    :param extra_params: Additional query parameters to pass to the API (e.g. {"stage": "active"}).
    :return: A RunbookListResponse object containing a list of runbooks.
    """
    client = client_mgr.get_client()

    path: str | None = "core/runbooks"
    params: dict[str, Any] = {"workspace_id": workspace_id}
    if is_template is not None:
        params["is_template"] = str(is_template).lower()
    if archived is not None:
        params["archived"] = str(archived).lower()
    if source_runbook_id is not None:
        params["source_runbook_id"] = source_runbook_id
    if folder_id is not None:
        params["folder_id"] = folder_id
    if extra_params:
        for key, value in extra_params.items():
            if key not in params:
                params[key] = value

    initial_params = dict(params)
    all_data: list[dict[str, Any]] = []
    last_response: dict[str, Any] = {}

    while path:
        response = await client.request("GET", path, params=params)
        params = None
        all_data.extend(response.get("data", []))
        last_response = response
        path = response.get("links", {}).get("next")

    return RunbookListResponse(
        **{
            "data": all_data,
            "included": last_response.get("included", []),
            "meta": last_response.get("meta", {"page": {"number": 1, "total": len(all_data)}}),
            "links": last_response.get("links", {"self": f"core/runbooks?{urlencode(initial_params)}"}),
        }
    )


@mcp.tool()
@inject_return_schema
async def get_runbook_tasks(
    runbook_id: str,
    forecast: bool = False,
    fields_task: list[str] | None = None,
    stage: list[str] | None = None,
    stream_id: list[str] | None = None,
    completion_type: str | None = None,
    task_type_id: list[str] | None = None,
    level: str | None = None,
    search_term: str | None = None,
    has_comments: bool | None = None,
    runbook_team_id: list[str] | None = None,
    user_id: list[str] | None = None,
    source_runbook_id: list[str] | None = None,
    sort: str | None = None,
) -> TaskListResponse:
    """
    Fetch tasks for a specific runbook, with optional filtering and sorting.

    This endpoint has two modes:
    - Conventional mode: supports filtering, pagination, and sorting.
    - Forecast mode (forecast=true): returns ALL tasks in a single response regardless of
      pagination or filters, and includes computed timing fields start_display and end_display,
      plus predecessor/successor graph relationships. Use for timeline or dependency views.

    :param runbook_id: The unique identifier for the runbook.
    :param forecast: When true, returns all tasks with computed forecast fields (start_display,
        end_display) and graph info (predecessors, successors). Overrides pagination and filters.
    :param fields_task: Specific task fields to return (maps to fields[task]). Reduces payload
        size. Attributes: created_at, comments_count, completion_type, custom_field_values,
        description, disable_notify, duration, elapsed_duration, is_late, end_actual,
        end_display (forecast only), end_fixed, end_planned, end_requirements, level, message,
        name, start_actual, start_display (forecast only), start_requirements, start_fixed,
        start_planned, start_ready, updated_at, stage. Relationships: predecessors,
        source_runbook, source_task, successors, stream, task_type.
    :param stage: Filter by task stage(s). Allowed: default, startable, in_progress, complete.
    :param stream_id: Filter to tasks in these stream ID(s).
    :param completion_type: Filter by completion type. Allowed: complete_normal,
        complete_skipped, complete_abandoned, complete_auto.
    :param task_type_id: Filter to tasks of these task type ID(s).
    :param level: Filter by task level.
    :param search_term: Filter tasks by search term matched against task name.
    :param has_comments: When true, return only tasks that have comments.
    :param runbook_team_id: Filter to tasks assigned to these runbook team ID(s).
    :param user_id: Filter to tasks assigned to these user ID(s).
    :param source_runbook_id: Filter to tasks originating from these source runbook ID(s).
    :param sort: Sort order. Example: start_planned or -start_planned (descending).
    :return: A TaskListResponse object containing a list of tasks for the specified runbook.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```

    """
    client = client_mgr.get_client()

    params: dict[str, Any] = {}
    if forecast:
        params["forecast"] = "true"
    if fields_task is not None:
        params["fields[task]"] = ",".join(fields_task)
    if stage:
        params["stage"] = ",".join(stage)
    if stream_id:
        params["stream_id"] = ",".join(stream_id)
    if completion_type is not None:
        params["completion_type"] = completion_type
    if task_type_id:
        params["task_type_id"] = ",".join(task_type_id)
    if level is not None:
        params["level"] = level
    if search_term:
        params["search_term"] = search_term
    if has_comments is not None:
        params["has_comments"] = str(has_comments).lower()
    if runbook_team_id:
        params["runbook_team_id"] = ",".join(runbook_team_id)
    if user_id:
        params["user_id"] = ",".join(user_id)
    if source_runbook_id:
        params["source_runbook_id"] = ",".join(source_runbook_id)
    if sort is not None:
        params["sort"] = sort

    # Forecast mode returns all tasks in a single response — no pagination needed
    if forecast:
        response = await client.request("GET", f"core/runbooks/{runbook_id}/tasks", params=params or None)
        return TaskListResponse(**response)

    path: str | None = f"core/runbooks/{runbook_id}/tasks"
    all_data: list[dict[str, Any]] = []
    last_response: dict[str, Any] = {}

    while path:
        response = await client.request("GET", path, params=params)
        params = None
        all_data.extend(response.get("data", []))
        last_response = response
        path = response.get("links", {}).get("next")

    return TaskListResponse(
        **{
            "data": all_data,
            "meta": last_response.get("meta", {"page": {"number": 1, "total": len(all_data)}}),
            "links": last_response.get("links", {"self": f"core/runbooks/{runbook_id}/tasks"}),
        }
    )


@mcp.tool()
async def update_runbook(
    runbook_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    is_template: bool | None = None,
    rto: int | None = None,
    timezone: str | None = None,
    rto_end_task: str | None = None,
    rto_start_task: str | None = None,
    custom_field_values: list[dict] | None = None,
) -> RunbookResponse:
    """
    Update a specific runbook's fields.

    :param runbook_id: The unique identifier for the runbook (required).
    :param name: The new name for the runbook (optional).
    :param description: The new description for the runbook (optional).
    :param status: The new RAG status for the runbook (Allowed: off, red, amber, green).
    :param is_template: Whether the runbook is a template (optional, true/false).
    :param rto: Recovery Time Objective in seconds (optional).
    :param timezone: IANA Timezone name (optional).
    :param rto_start_task: ID of the start task for RTO/RTA feature (optional, relationship field).
    :param rto_end_task: ID of the end task for RTO/RTA feature (optional, relationship field).
    :param custom_field_values: List of custom field values to update. Each item should be a dict with
        either {"name": "Field Name", "value": "value"} or {"custom_field_id": "123", "value": "value"}.
        Value can be a string or list of strings for multi-select fields.
    :return: A RunbookResponse object representing the updated runbook.
    """
    client = client_mgr.get_client()
    attributes = {}
    if name is not None:
        attributes["name"] = name
    if description is not None:
        attributes["description"] = description
    if status is not None:
        attributes["status"] = status
    if is_template is not None:
        attributes["is_template"] = is_template
    if rto is not None:
        attributes["rto"] = rto
    if timezone is not None:
        attributes["timezone"] = timezone
    if custom_field_values is not None:
        attributes["custom_field_values"] = custom_field_values

    relationships = {}
    if rto_start_task is not None:
        relationships["rto_start_task"] = {"data": {"type": "task", "id": rto_start_task}}
    if rto_end_task is not None:
        relationships["rto_end_task"] = {"data": {"type": "task", "id": rto_end_task}}

    payload = {
        "data": {
            "type": "runbook",
            "id": runbook_id,
            "attributes": attributes,
        }
    }
    if relationships:
        payload["data"]["relationships"] = relationships

    response = await client.request("PATCH", f"core/runbooks/{runbook_id}", json_data=payload)
    return RunbookResponse(**response)


@mcp.tool()
async def create_runbook(
    name: str,
    workspace_id: str | None = None,
    description: str = "",
    status: str | None = None,
    is_template: bool | None = None,
    template_type: str | None = None,
    rto: int | None = None,
    timezone: str | None = None,
    rto_end_task: str | None = None,
    rto_start_task: str | None = None,
    runbook_type_id: str | None = None,
    folder_id: str | None = None,
    copy_source_runbook_id: str | None = None,
    copy_tasks: bool | None = None,
    copy_teams: bool | None = None,
    copy_users: bool | None = None,
    shift_fixed_times: bool | None = None,
) -> RunbookResponse:
    """
    Create a new runbook in a workspace, or as a copy of an existing runbook/template.

    :param name: The name of the new runbook.
    :param workspace_id: The ID of the workspace to create the runbook in (relationship field).
        Required unless copy_source_runbook_id is passed.
    :param description: An optional description for the runbook.
    :param status: The new RAG status for the runbook (Allowed: off, red, amber, green).
    :param is_template: Whether the runbook is a template (optional, true/false).
    :param template_type: The template type of the runbook. Allowed values: off, default, snippet.
    :param rto: Recovery Time Objective (RTO) in seconds (optional).
    :param timezone: IANA Timezone name (optional).
    :param runbook_type_id: The ID of the runbook type to associate with this runbook (optional, relationship field).
    :param rto_start_task: ID of the start task for RTO/RTA feature (optional, relationship field).
    :param rto_end_task: ID of the end task for RTO/RTA feature (optional, relationship field).
    :param folder_id: ID of the folder to place the new runbook in (optional, relationship field).
        If omitted, the runbook lands in the workspace's default location.
    :param copy_source_runbook_id: ID of an existing runbook/template to copy from. When set, this
        runbook is created as a copy and workspace_id may be omitted. The copy flags below all default
        to a full clone; only set one to False when the user asks to exclude that part.
    :param copy_tasks: Whether to copy the source's tasks. Defaults to True.
    :param copy_teams: Whether to copy the source's teams. Defaults to True. Teams are copied without
        their members unless copy_users is also True, so keep teams and users together.
    :param copy_users: Whether to copy the source's users. Defaults to True.
    :param shift_fixed_times: When copying, whether start_fixed/end_fixed task attributes should be
        recalculated relative to the new runbook's start.
    :return: A RunbookResponse object representing the newly created runbook.
    """
    client = client_mgr.get_client()
    attributes = {"name": name, "description": description}
    if status is not None:
        attributes["status"] = status
    if is_template is not None:
        attributes["is_template"] = is_template
    if template_type is not None:
        attributes["template_type"] = template_type
    if rto is not None:
        attributes["rto"] = rto
    if timezone is not None:
        attributes["timezone"] = timezone

    relationships = {}
    if workspace_id is not None:
        relationships["workspace"] = {"data": {"type": "workspace", "id": workspace_id}}
    if runbook_type_id is not None:
        relationships["runbook_type"] = {"data": {"type": "runbook_type", "id": runbook_type_id}}
    if rto_start_task is not None:
        relationships["rto_start_task"] = {"data": {"type": "task", "id": rto_start_task}}
    if rto_end_task is not None:
        relationships["rto_end_task"] = {"data": {"type": "task", "id": rto_end_task}}
    if folder_id is not None:
        relationships["folder"] = {"data": {"type": "folder", "id": folder_id}}

    payload: dict[str, Any] = {
        "data": {
            "type": "runbook",
            "attributes": attributes,
        }
    }
    if relationships:
        payload["data"]["relationships"] = relationships

    meta: dict[str, Any] = {}
    if copy_source_runbook_id is not None:
        # Default to a full clone when the caller doesn't specify. The API flags default to
        meta["copy"] = {
            "source_runbook_id": copy_source_runbook_id,
            "tasks": copy_tasks if copy_tasks is not None else True,
            "teams": copy_teams if copy_teams is not None else True,
            "users": copy_users if copy_users is not None else True,
        }
    if shift_fixed_times is not None:
        meta["shift_fixed_times"] = shift_fixed_times
    if meta:
        payload["meta"] = meta

    response = await client.request("POST", "core/runbooks", json_data=payload)
    return RunbookResponse(**response)


@mcp.tool()
async def manage_runbook(
    runbook_id: str,
    action: Literal["start", "cancel", "pause", "resume"],
    comms: Literal["off", "test", "on"] = "off",
    disable_task_notify: bool | None = False,
    run_type: Literal["live", "rehearsal"] = "rehearsal",
    rebaseline: bool | None = False,
    shift_fixed_times: bool | None = False,
    validation_level: Literal["warning", "error"] | None = "error",
    message: str | None = None,
    notify: bool | None = False,
) -> dict[str, Any]:
    """
    Manage a specific runbook by performing an action (start, cancel, pause, resume).
    These are the only possible actions with this tool.

    :param runbook_id: The unique identifier for the runbook.
    :param action: The action to perform (start, cancel, pause, resume).
    :param comms: Communication mode (off, test, on) (for start). Required by the platform;
        defaults to "off" so a start does not send communications unless asked to.
    :param disable_task_notify: Disable task start notifications (for start).
    :param run_type: Type of run (live, rehearsal) (for start). Required by the platform;
        defaults to "rehearsal" — pass "live" explicitly to start a live run.
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


@mcp.tool()
async def get_runbook_template_copies(
    runbook_id: str,
) -> RunbookListResponse:
    """
    Get all runbooks that were created from a specific runbook template.

    :param runbook_id: The template runbook ID to find copies of.
    :return: A RunbookListResponse containing list of runbooks created from this template.
    """
    client = client_mgr.get_client()
    all_data: list[dict[str, Any]] = []

    # Build initial path with source_runbook_id filter
    path: str | None = f"core/runbooks?source_runbook_id={runbook_id}"

    # Handle pagination - fetch all pages
    while path:
        response = await client.request("GET", path)
        all_data.extend(response.get("data", []))
        path = response.get("links", {}).get("next")

    # Build final response with all collected data
    final_response = {
        "data": all_data,
        "meta": {"page": {"number": 1, "total": len(all_data)}},
        "links": {"self": f"core/runbooks?source_runbook_id={runbook_id}"},
    }
    return RunbookListResponse(**final_response)
