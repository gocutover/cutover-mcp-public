from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def get_runbook_teams(
    runbook_id: str,
) -> list[dict[str, Any]]:
    """
    Get all teams associated with a runbook.

    :param runbook_id: The runbook ID to fetch teams for.
    :return: List of team objects with id, team_id, name, and users_count.
    """
    client = client_mgr.get_client()
    teams: list[dict[str, Any]] = []

    # Build initial path
    path: str | None = f"core/runbooks/{runbook_id}/runbook_teams"

    # Handle pagination - fetch all pages
    while path:
        response = await client.request("GET", path)

        for team in response.get("data", []):
            attributes = team.get("attributes", {})
            relationships = team.get("relationships", {})
            meta = team.get("meta", {})

            # Get the underlying team ID from relationships
            team_data = relationships.get("team", {}).get("data", {})
            team_id = team_data.get("id") if team_data else None

            team_obj: dict[str, Any] = {
                "id": team.get("id"),
                "team_id": team_id,
                "name": attributes.get("name"),
                "users_count": meta.get("users_count", 0),
            }
            teams.append(team_obj)

        # Check for next page using links.next
        path = response.get("links", {}).get("next")

    return teams
