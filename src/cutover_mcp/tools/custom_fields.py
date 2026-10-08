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
    :return: Custom field metadata with id, name, field_type, field_options, required, apply_to, allow_field_creation.
    """
    client = await client_mgr.get_client()

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
