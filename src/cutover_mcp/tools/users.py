from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


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

    # Extract user data from JSON:API response
    user_data = response.get("data", {})
    attributes = user_data.get("attributes", {})

    # Build simplified user object with only requested fields
    first_name = attributes.get("first_name", "")
    last_name = attributes.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or attributes.get("name", "")

    user: dict[str, Any] = {
        "id": user_data.get("id"),
        "email": attributes.get("email"),
        "full_name": full_name,
    }

    return user
