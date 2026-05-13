from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


def _parse_user(user_data: dict[str, Any]) -> dict[str, Any]:
    attributes = user_data.get("attributes", {})
    first_name = attributes.get("first_name", "")
    last_name = attributes.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or attributes.get("name", "")
    return {
        "id": user_data.get("id"),
        "email": attributes.get("email"),
        "full_name": full_name,
    }


@mcp.tool()
async def get_user(
    user_id: str,
) -> dict[str, Any]:
    """
    Get user details by user ID.

    :param user_id: The user ID to fetch details for.
    :return: User details with id, email, and full_name.
    """
    client = client_mgr.get_client()
    response = await client.request("GET", f"core/users/{user_id}")
    return _parse_user(response.get("data", {}))


@mcp.tool()
async def search_users(
    query: str,
) -> list[dict[str, Any]]:
    """
    Search for users by name or email (fuzzy match).

    :param query: Search string (name or email, partial match).
    :return: List of matching users, each with id, email, and full_name.
    """
    client = client_mgr.get_client()
    response = await client.request("GET", "core/users", params={"query": query})
    return [_parse_user(user_data) for user_data in response.get("data", [])]
