from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def list_custom_fields(
    workspace_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    List all available custom fields to discover fields that may not have values yet.

    :param workspace_id: Optional workspace ID to filter custom fields. If not provided,
        returns fields from all accessible workspaces.
    :return: List of custom fields with id, name, field_type, field_options, required, apply_to, allow_field_creation.
    """
    client = client_mgr.get_client()

    path: str | None = "core/custom_fields"
    params: dict[str, Any] | None = {}
    if workspace_id:
        params["workspace_id"] = workspace_id

    custom_fields: list[dict[str, Any]] = []

    while path:
        response = await client.request("GET", path, params=params)
        params = None

        for item in response.get("data", []):
            attributes = item.get("attributes", {})

            # Skip archived fields
            if attributes.get("archived", False):
                continue

            custom_field: dict[str, Any] = {
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
            custom_fields.append(custom_field)

        # Use cursor-based pagination via links.next
        path = response.get("links", {}).get("next")

    return custom_fields


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
