from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def get_activities(
    runbook_id: str,
    created_after: str | None = None,
    created_before: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get activities for an incident runbook to track recent actions and events.

    :param runbook_id: The runbook ID to retrieve activities for.
    :param created_after: Filter activities after this date (ISO 8601, e.g., "2025-01-01T00:00:00Z").
    :param created_before: Filter activities before this date (ISO 8601, e.g., "2025-12-31T23:59:59Z").
    :return: List of activity entries with id, key, starred, created_at, changes, description, etc.
    """
    client = client_mgr.get_client()
    activities: list[dict[str, Any]] = []

    params: dict[str, str] = {"runbook_id": runbook_id}
    if created_after:
        params["created_after"] = created_after
    if created_before:
        params["created_before"] = created_before

    # Fetch all pages using cursor-based pagination
    # params passed on first request; subsequent requests follow links.next verbatim
    path: str | None = "core/activities"
    while path:
        response = await client.request("GET", path, params=params)
        params = None

        # Extract and format activities from current page
        for activity in response.get("data", []):
            attributes = activity.get("attributes", {})
            relationships = activity.get("relationships", {})
            meta = activity.get("meta", {})

            activity_entry: dict[str, Any] = {
                "id": activity.get("id"),
                "key": attributes.get("key"),
                "starred": attributes.get("starred", False),
                "created_at": attributes.get("created_at"),
                "changes": attributes.get("changes"),
            }

            # Add description from meta.message.plain if present
            if meta and "message" in meta:
                message = meta.get("message", {})
                if isinstance(message, dict) and "plain" in message:
                    activity_entry["description"] = message.get("plain")

            # Add activist info if present
            activist_data = relationships.get("activist", {}).get("data", {})
            if activist_data:
                activity_entry["activist_id"] = activist_data.get("id")
                activity_entry["activist_type"] = activist_data.get("type")

            # Add trackable info if present
            trackable_data = relationships.get("trackable", {}).get("data", {})
            if trackable_data:
                activity_entry["trackable_id"] = trackable_data.get("id")
                activity_entry["trackable_type"] = trackable_data.get("type")

            # Add recipient info if present
            recipient_data = relationships.get("recipient", {}).get("data", {})
            if recipient_data:
                activity_entry["recipient_id"] = recipient_data.get("id")
                activity_entry["recipient_type"] = recipient_data.get("type")

            activities.append(activity_entry)

        # Use cursor-based pagination via links.next
        path = response.get("links", {}).get("next")

    return activities
