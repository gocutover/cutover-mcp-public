from typing import Any, Literal

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr

# apply_to slugs grouped by resource type; used for client-side scope filtering.
TASK_APPLY_TO = ["task_edit", "task_start", "task_end", "task_add_edit"]
RUNBOOK_APPLY_TO = ["runbook_add_edit", "runbook_edit"]


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
        "runbook" for runbook-level fields only, "all" (default) for everything.
    :return: List of custom fields with id, name, field_type, field_options, required,
        apply_to, allow_field_creation, default_value, display_name. Dependent (child)
        fields of searchable/structured parents are nested under their parent's
        dependent_fields key rather than listed as separate top-level entries.
    """
    client = client_mgr.get_client()

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
        return custom_fields

    allowed = set(TASK_APPLY_TO if scope == "task" else RUNBOOK_APPLY_TO)
    return [field for field in custom_fields if field.get("apply_to") in allowed]


@mcp.tool()
async def get_custom_field(
    custom_field_id: str,
) -> dict[str, Any]:
    """
    Get a custom field's metadata including its type and valid options.

    :param custom_field_id: The ID of the custom field to retrieve.
    :return: Custom field metadata with id, name, field_type, field_options, required, apply_to, allow_field_creation.
    """
    client = client_mgr.get_client()

    response = await client.request("GET", f"core/custom_fields/{custom_field_id}")

    # Extract and flatten the response
    data = response.get("data", {})
    attributes = data.get("attributes", {})

    custom_field: dict[str, Any] = {
        "id": data.get("id"),
        "name": attributes.get("name"),
        "field_type": attributes.get("field_type"),
        "field_options": attributes.get("field_options", []),
        "required": attributes.get("required", False),
        "apply_to": attributes.get("apply_to"),
        "allow_field_creation": attributes.get("allow_field_creation", False),
        "default_value": attributes.get("default_value"),
        "display_name": attributes.get("display_name"),
    }

    return custom_field
