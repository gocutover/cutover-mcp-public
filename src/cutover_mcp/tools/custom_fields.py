from typing import Any, Literal

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr

# apply_to slugs grouped by resource type; used for client-side scope filtering.
TASK_APPLY_TO = ["task_edit", "task_start", "task_end", "task_add_edit"]
# The runbook scope includes the dashboard fields shown on the runbook homepage, the
# Post-Implementation Review (PIR) and the Incident Review. Their values are stored on the
# runbook and are written with update_runbook.
RUNBOOK_APPLY_TO = [
    "runbook_add_edit",
    "runbook_edit",
    "runbook_page",
    "pir_summary",
    "pir_value_select",
    "incident_review_content",
]
# Scopes that are never returned: runbook_end belongs to a deprecated feature, and project-level
# fields do not apply to runbooks or tasks. scope="all" filters on this list rather than on an
# allowlist, so any new scopes the Cutover API introduces are returned without a code change.
EXCLUDED_APPLY_TO = ["runbook_end", "project_add_edit", "project_edit"]


def _build_field(item: dict[str, Any]) -> dict[str, Any]:
    """Flatten a JSON:API custom field resource into a plain dict."""
    attributes = item.get("attributes", {})
    return {
        "id": item.get("id"),
        "name": attributes.get("name"),
        "field_type": attributes.get("field_type"),
        "field_options": attributes.get("field_options", []),
        "required": attributes.get("required", False),
        "apply_to": attributes.get("apply_to"),
        "allow_field_creation": attributes.get("allow_field_creation", False),
        "default_value": attributes.get("default_value"),
        "display_name": attributes.get("display_name"),
    }


@mcp.tool()
async def list_custom_fields(
    workspace_id: str | None = None,
    include_global: bool = True,
    scope: Literal["all", "task", "runbook"] = "all",
) -> list[dict[str, Any]]:
    """
    List all available custom fields to discover fields that may not have values yet.

    :param workspace_id: Optional workspace ID to filter custom fields. If not provided,
        returns fields from all accessible workspaces.
    :param include_global: When workspace_id is provided, also include globally available
        (shared) custom fields alongside the workspace's own. Set to False to return only
        workspace-specific fields.
    :param scope: Which custom fields to return: "task" for task-level fields only,
        "runbook" for runbook-level fields only, or "all" (default) for fields of every scope
        except the deprecated runbook_end scope and project-level scopes, which are never
        returned. The runbook scope includes the dashboard fields on the runbook homepage (e.g.
        Executive summary, Additional notes), the Post-Implementation Review (PIR) and the
        Incident Review (e.g. Incident Summary, RCA, Lessons Learned), all of which are set with
        update_runbook.
    :return: List of custom fields with id, name, field_type, field_options, required,
        apply_to, allow_field_creation, default_value, display_name. Dependent (child)
        fields of searchable/structured parents are nested under their parent's
        dependent_fields key rather than listed as separate top-level entries.
        apply_to identifies where a field is used: task_edit, task_start, task_end and
        task_add_edit for tasks; runbook_add_edit and runbook_edit for runbooks; runbook_page
        (homepage), pir_summary and pir_value_select (PIR), and incident_review_content
        (Incident Review) for runbook dashboards.

    When looking up a field by the name a user gives, compare it against both ``name`` and
    ``display_name``. Dashboard fields often have an internal ``name`` (for example
    ``dashboard:incident_review:lessons_learned``) that differs from the label users see
    (``display_name``: "Lessons Learned"). When writing values, identify the field by its
    ``id``, passed as ``custom_field_id``.
    """
    client = await client_mgr.get_client()

    path: str | None = "core/custom_fields"
    params: dict[str, Any] | None = {}
    if workspace_id:
        params["workspace_id"] = workspace_id
        # workspace_id + global=true returns the workspace's own fields plus global ones.
        params["global"] = "true" if include_global else "false"

    # Collect all pages first so parent/child relationships can be resolved across page boundaries.
    raw_items: list[dict[str, Any]] = []
    while path:
        response = await client.request("GET", path, params=params)
        params = None
        raw_items.extend(response.get("data", []))

        # Use cursor-based pagination via links.next
        path = response.get("links", {}).get("next")

    # Nest dependent (child) fields under their parent instead of listing them separately.
    parsed: dict[str, dict[str, Any]] = {}
    dependents_of: dict[str, list[str]] = {}
    child_ids: set[str] = set()

    for item in raw_items:
        attributes = item.get("attributes", {})

        # Skip archived fields (core archives dependent children together with their parent)
        if attributes.get("archived", False):
            continue

        field_id = item.get("id")
        if field_id is None:
            continue
        parsed[field_id] = _build_field(item)

        dependent_data = ((item.get("relationships") or {}).get("dependent_custom_fields") or {}).get("data") or []
        dependent_ids = [d.get("id") for d in dependent_data if d.get("id")]
        if dependent_ids:
            dependents_of[field_id] = dependent_ids
            child_ids.update(dependent_ids)

    custom_fields: list[dict[str, Any]] = []
    for field_id, field in parsed.items():
        # A dependent child is represented under its parent, not at the top level.
        if field_id in child_ids:
            continue
        dependent_ids = dependents_of.get(field_id)
        if dependent_ids:
            field["dependent_fields"] = [parsed[cid] for cid in dependent_ids if cid in parsed]
        custom_fields.append(field)

    if scope == "all":
        excluded = set(EXCLUDED_APPLY_TO)
        return [field for field in custom_fields if field.get("apply_to") not in excluded]

    allowed = set(TASK_APPLY_TO if scope == "task" else RUNBOOK_APPLY_TO)
    return [field for field in custom_fields if field.get("apply_to") in allowed]


@mcp.tool()
async def get_custom_field(
    custom_field_id: str,
) -> dict[str, Any]:
    """
    Get a custom field's metadata including its type and valid options.

    :param custom_field_id: The ID of the custom field to retrieve.
    :return: Custom field metadata with id, name, field_type, field_options, required, apply_to,
        allow_field_creation, default_value, display_name, global, archived,
        custom_field_group_id, task_type_ids and runbook_type_ids. workspace_id is always None
        here because the API leaves the workspace out of this response.
    """
    client = await client_mgr.get_client()

    response = await client.request("GET", f"core/custom_fields/{custom_field_id}")
    return _build_field_detail(response.get("data", {}))


# Field types that can be created through these tools. searchable, multi_searchable and endpoint
# fields need an integration data source configured in the Cutover UI, so they are left out.
CreatableFieldType = Literal["text", "textarea", "select_menu", "radiobox", "checkboxes", "datetime", "user_select"]
OPTION_FIELD_TYPES = {"select_menu", "radiobox", "checkboxes"}
CreatableApplyTo = Literal[
    "runbook_add_edit",
    "runbook_edit",
    "runbook_page",
    "task_add_edit",
    "task_edit",
    "task_start",
    "task_end",
]


def _build_field_detail(item: dict[str, Any]) -> dict[str, Any]:
    """_build_field plus the scope and grouping a caller needs to confirm a write."""
    field = _build_field(item)
    attributes = item.get("attributes", {})
    relationships = item.get("relationships") or {}
    field["global"] = attributes.get("global")
    field["archived"] = attributes.get("archived", False)
    field["workspace_id"] = ((relationships.get("workspace") or {}).get("data") or {}).get("id")
    field["custom_field_group_id"] = ((relationships.get("custom_field_group") or {}).get("data") or {}).get("id")
    constraints = (relationships.get("constraints") or {}).get("data") or []
    field["task_type_ids"] = [c["id"] for c in constraints if c.get("type") == "task_type"]
    field["runbook_type_ids"] = [c["id"] for c in constraints if c.get("type") == "runbook_type"]
    return field


async def _read_back(client: Any, written: dict[str, Any]) -> dict[str, Any]:
    """Fetch the field after a write and merge it with the write response.

    The two responses each leave out a relationship: POST/PATCH omit custom_field_group and GET
    omits workspace. The GET is the stored state; the workspace comes from the write response.
    """
    response = await client.request("GET", f"core/custom_fields/{written.get('id')}")
    field = _build_field_detail(response.get("data", {}))
    if field["workspace_id"] is None:
        field["workspace_id"] = _build_field_detail(written)["workspace_id"]
    return field


def _constraints(
    task_type_ids: list[str] | None,
    runbook_type_ids: list[str] | None,
) -> list[dict[str, str]]:
    constraints = [{"id": str(i), "type": "task_type"} for i in task_type_ids or []]
    constraints += [{"id": str(i), "type": "runbook_type"} for i in runbook_type_ids or []]
    return constraints


@mcp.tool()
async def create_custom_field(
    name: str,
    field_type: CreatableFieldType,
    apply_to: CreatableApplyTo,
    workspace_id: str | None = None,
    global_field: bool = False,
    field_options: list[str] | None = None,
    required: bool | None = None,
    default_value: str | None = None,
    allow_field_creation: bool | None = None,
    display_list: bool | None = None,
    display_search: bool | None = None,
    display_table: bool | None = None,
    custom_field_group_id: str | None = None,
    task_type_ids: list[str] | None = None,
    runbook_type_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a custom field definition (the Custom Fields admin page). This defines a new field;
    to set a value on a runbook or task, use custom_field_values on the runbook and task tools.

    Requires the Custom Fields Admin role (or Global Admin). Check list_custom_fields first so
    an existing field is reused rather than duplicated.

    :param name: The field's name.
    :param field_type: text, textarea, select_menu, radiobox, checkboxes, datetime or user_select.
    :param apply_to: Where the field appears: runbook_add_edit / runbook_edit (runbook details),
        runbook_page (runbook homepage), task_add_edit / task_edit (task details), task_start or
        task_end (asked when a task starts or finishes).
    :param workspace_id: The workspace that owns the field. Required unless global_field is True.
    :param global_field: Create the field for every workspace on the instance. Must be set
        explicitly, and only when the user asks for a global field, since every workspace sees it.
    :param field_options: Option names. Required for select_menu, radiobox and checkboxes, and
        not allowed for other field types.
    :param required: Whether a value must be given.
    :param default_value: The value a new runbook or task starts with.
    :param allow_field_creation: Let users add options from within a runbook.
    :param display_list: Show the value as a pill in runbook and task lists.
    :param display_search: Allow filtering by this field.
    :param display_table: Include the field in table views.
    :param custom_field_group_id: The group to show the field in (see list_custom_field_groups).
    :param task_type_ids: Limit a task field to these task types (see list_task_types).
    :param runbook_type_ids: Limit the field to these runbook types (see list_runbook_types).
    :return: The created field: id, name, field_type, field_options, required, apply_to,
        allow_field_creation, default_value, display_name, global, archived, workspace_id,
        custom_field_group_id, task_type_ids, runbook_type_ids. display_name always equals
        name for fields created this way; the API does not accept a separate label.
    """
    if bool(workspace_id) == global_field:
        raise ValueError("Pass exactly one of workspace_id or global_field=True.")
    if field_type in OPTION_FIELD_TYPES and not field_options:
        raise ValueError(f"field_options is required for a {field_type} field.")
    if field_type not in OPTION_FIELD_TYPES and field_options:
        raise ValueError(f"field_options is only allowed for select_menu, radiobox and checkboxes, not {field_type}.")

    attributes: dict[str, Any] = {
        "name": name,
        "field_type": field_type,
        "apply_to": apply_to,
        "global": global_field,
    }
    if field_options:
        attributes["field_options"] = [{"name": option} for option in field_options]
    optional = {
        "required": required,
        "default_value": default_value,
        "allow_field_creation": allow_field_creation,
        "display_list": display_list,
        "display_search": display_search,
        "display_table": display_table,
    }
    attributes.update({key: value for key, value in optional.items() if value is not None})

    relationships: dict[str, Any] = {}
    if workspace_id:
        relationships["workspace"] = {"data": {"id": workspace_id, "type": "workspace"}}
    if custom_field_group_id:
        relationships["custom_field_group"] = {"data": {"id": custom_field_group_id, "type": "custom_field_group"}}
    constraints = _constraints(task_type_ids, runbook_type_ids)
    if constraints:
        relationships["constraints"] = {"data": constraints}

    payload: dict[str, Any] = {"data": {"type": "custom_field", "attributes": attributes}}
    if relationships:
        payload["data"]["relationships"] = relationships

    client = await client_mgr.get_client()
    response = await client.request("POST", "core/custom_fields", json_data=payload)
    return await _read_back(client, response.get("data", {}))


@mcp.tool()
async def update_custom_field(
    custom_field_id: str,
    name: str | None = None,
    add_field_options: list[str] | None = None,
    required: bool | None = None,
    default_value: str | None = None,
    allow_field_creation: bool | None = None,
    display_list: bool | None = None,
    display_search: bool | None = None,
    display_table: bool | None = None,
    custom_field_group_id: str | None = None,
    task_type_ids: list[str] | None = None,
    runbook_type_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Update a custom field definition. Only the parameters you pass are changed. The field's
    type, apply_to and workspace cannot be changed; create a new field instead.

    Requires the Custom Fields Admin role (or Global Admin).

    :param custom_field_id: The ID of the field to update (from list_custom_fields).
    :param name: The new name.
    :param add_field_options: Option names to add to a select_menu, radiobox or checkboxes field.
        Existing options are kept. Options cannot be renamed or removed through the API.
    :param required: Whether a value must be given.
    :param default_value: The value a new runbook or task starts with.
    :param allow_field_creation: Let users add options from within a runbook.
    :param display_list: Show the value as a pill in runbook and task lists.
    :param display_search: Allow filtering by this field.
    :param display_table: Include the field in table views.
    :param custom_field_group_id: Move the field into this group. Pass "" to take it out of its
        group. When omitted the field stays in its current group.
    :param task_type_ids: Replace the task type constraints with these task types. The runbook
        type constraints are kept.
    :param runbook_type_ids: Replace the runbook type constraints with these runbook types. The
        task type constraints are kept. The Cutover API rejects an empty constraint list, so
        constraints cannot be cleared here; archive the field and create a new one instead.
    :return: The updated field, in the same shape as create_custom_field.
    """
    if task_type_ids == [] or runbook_type_ids == []:
        raise ValueError("Constraints cannot be cleared through the API; pass at least one id, or omit the parameter.")

    attributes: dict[str, Any] = {}
    if add_field_options:
        attributes["field_options"] = [{"name": option} for option in add_field_options]
    optional = {
        "name": name,
        "required": required,
        "default_value": default_value,
        "allow_field_creation": allow_field_creation,
        "display_list": display_list,
        "display_search": display_search,
        "display_table": display_table,
    }
    attributes.update({key: value for key, value in optional.items() if value is not None})

    changes_constraints = task_type_ids is not None or runbook_type_ids is not None
    if not attributes and custom_field_group_id is None and not changes_constraints:
        raise ValueError("Pass at least one field to update.")

    client = await client_mgr.get_client()
    current_response = await client.request("GET", f"core/custom_fields/{custom_field_id}")
    current = _build_field_detail(current_response.get("data", {}))

    if add_field_options and current["field_type"] not in OPTION_FIELD_TYPES:
        raise ValueError(
            f"add_field_options is only allowed for select_menu, radiobox and checkboxes, not {current['field_type']}."
        )

    # A PATCH that leaves out custom_field_group removes the field from its group, so the
    # current group is sent again unless the caller passes a new group, or "" to remove it.
    relationships: dict[str, Any] = {}
    group_id = current["custom_field_group_id"] if custom_field_group_id is None else custom_field_group_id
    if group_id:
        relationships["custom_field_group"] = {"data": {"id": group_id, "type": "custom_field_group"}}
    elif custom_field_group_id == "":
        relationships["custom_field_group"] = {"data": None}

    # The constraints relationship is replaced as a whole, so the type the caller left out is
    # sent again from the current field.
    if changes_constraints:
        relationships["constraints"] = {
            "data": _constraints(
                current["task_type_ids"] if task_type_ids is None else task_type_ids,
                current["runbook_type_ids"] if runbook_type_ids is None else runbook_type_ids,
            )
        }

    # The API answers a PATCH with empty attributes with 400, so a relationship-only update
    # sends the current name.
    if not attributes:
        attributes["name"] = current["name"]

    payload: dict[str, Any] = {"data": {"type": "custom_field", "id": custom_field_id, "attributes": attributes}}
    if relationships:
        payload["data"]["relationships"] = relationships

    response = await client.request("PATCH", f"core/custom_fields/{custom_field_id}", json_data=payload)
    return await _read_back(client, response.get("data", {}))


@mcp.tool()
async def archive_custom_field(custom_field_id: str) -> dict[str, Any]:
    """
    Archive a custom field so it can no longer be used. Existing values stay on runbooks and
    tasks. Requires the Custom Fields Admin role (or Global Admin).

    :param custom_field_id: The ID of the field to archive (from list_custom_fields).
    :return: {"id": custom_field_id, "archived": True} on success.
    """
    client = await client_mgr.get_client()
    await client.request("PATCH", f"core/custom_fields/{custom_field_id}/archive")
    return {"id": custom_field_id, "archived": True}


def _build_group(item: dict[str, Any]) -> dict[str, Any]:
    attributes = item.get("attributes", {})
    return {
        "id": item.get("id"),
        "name": attributes.get("name"),
        "default": attributes.get("default", False),
    }


@mcp.tool()
async def list_custom_field_groups() -> list[dict[str, Any]]:
    """
    List custom field groups, which control the section a custom field is shown in. Archived
    groups are not returned; the API does not list them.

    :return: List of groups with id, name and default.
    """
    client = await client_mgr.get_client()

    path: str | None = "core/custom_field_groups"
    groups: list[dict[str, Any]] = []
    while path:
        response = await client.request("GET", path)
        groups.extend(_build_group(item) for item in response.get("data", []))
        path = response.get("links", {}).get("next")

    return groups


@mcp.tool()
async def create_custom_field_group(name: str) -> dict[str, Any]:
    """
    Create a custom field group. Groups are shared across the instance. Check
    list_custom_field_groups first so an existing group is reused. Requires the Custom Fields
    Admin role (or Global Admin).

    :param name: The group's name.
    :return: The created group with id, name and default.
    """
    client = await client_mgr.get_client()
    payload = {"data": {"type": "custom_field_group", "attributes": {"name": name}}}
    response = await client.request("POST", "core/custom_field_groups", json_data=payload)
    return _build_group(response.get("data", {}))


@mcp.tool()
async def update_custom_field_group(custom_field_group_id: str, name: str) -> dict[str, Any]:
    """
    Rename a custom field group. Requires the Custom Fields Admin role (or Global Admin).

    :param custom_field_group_id: The ID of the group (from list_custom_field_groups).
    :param name: The new name.
    :return: The updated group with id, name and default.
    """
    client = await client_mgr.get_client()
    payload = {"data": {"type": "custom_field_group", "id": custom_field_group_id, "attributes": {"name": name}}}
    response = await client.request("PATCH", f"core/custom_field_groups/{custom_field_group_id}", json_data=payload)
    return _build_group(response.get("data", {}))


@mcp.tool()
async def archive_custom_field_group(custom_field_group_id: str) -> dict[str, Any]:
    """
    Archive a custom field group. Requires the Custom Fields Admin role (or Global Admin).

    :param custom_field_group_id: The ID of the group (from list_custom_field_groups).
    :return: {"id": custom_field_group_id, "archived": True} on success.
    """
    client = await client_mgr.get_client()
    await client.request("PATCH", f"core/custom_field_groups/{custom_field_group_id}/archive")
    return {"id": custom_field_group_id, "archived": True}
