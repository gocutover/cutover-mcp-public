from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr

DEFAULT_MAX_PAGES = 10


@mcp.tool()
async def get_action_logs(
    runbook_id: str | None = None,
    user_id: str | None = None,
    workspace_id: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> dict[str, Any]:
    """
    Retrieve action logs (audit logs) from Cutover. Paginates through results up to max_pages.

    :param runbook_id: The runbook ID to filter action logs by.
    :param user_id: Optional user ID to filter action logs by a specific user.
    :param workspace_id: Optional workspace ID to filter action logs by workspace.
    :param created_after: Filter logs after this date (ISO 8601, e.g., "2025-01-01T00:00:00Z").
    :param created_before: Filter logs before this date (ISO 8601, e.g., "2025-12-31T23:59:59Z").
    :param max_pages: Maximum number of pages to fetch (default 10, must be at least 1).
    :return: Dict with "action_logs" (list of entries with id, event, description, changes,
        created_at, author, and resource info), "pages_fetched", and "truncated" (true when
        more pages exist beyond max_pages — narrow the date range or raise max_pages to
        retrieve them).
    """
    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")

    client = client_mgr.get_client()
    action_logs: list[dict[str, Any]] = []

    params: dict[str, Any] | None = {}

    if runbook_id:
        params["runbook_id"] = runbook_id
    if user_id:
        params["user_id"] = user_id
    if workspace_id:
        params["workspace_id"] = workspace_id
    if created_after:
        params["created_after"] = created_after
    if created_before:
        params["created_before"] = created_before

    path: str | None = "core/action_logs"
    pages_fetched = 0

    # Cursor-based pagination, bounded by max_pages
    # params passed on first request; subsequent requests follow links.next verbatim
    while path and pages_fetched < max_pages:
        response = await client.request("GET", path, params=params)
        params = None
        pages_fetched += 1

        for log in response.get("data", []):
            attributes = log.get("attributes", {})
            relationships = log.get("relationships", {})

            action_log_entry: dict[str, Any] = {
                "id": log.get("id"),
                "event": attributes.get("event"),
                "description": attributes.get("description"),
                "changes": attributes.get("changes"),
                "created_at": attributes.get("created_at"),
            }

            # Add author info if present
            author_data = relationships.get("author", {}).get("data", {})
            if author_data:
                action_log_entry["author_id"] = author_data.get("id")
                action_log_entry["author_type"] = author_data.get("type")

            # Add resource info if present
            resource_data = relationships.get("resource", {}).get("data", {})
            if resource_data:
                action_log_entry["resource_id"] = resource_data.get("id")
                action_log_entry["resource_type"] = resource_data.get("type")

            action_logs.append(action_log_entry)

        path = response.get("links", {}).get("next")

    return {
        "action_logs": action_logs,
        "pages_fetched": pages_fetched,
        "truncated": bool(path),
    }
