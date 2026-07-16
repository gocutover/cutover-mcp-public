from unittest.mock import AsyncMock

import httpx
import pytest

from cutover_mcp.tools import teams


@pytest.mark.asyncio
async def test_get_runbook_teams_basic(mock_client_manager):
    """Test fetching teams for a runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "rt-1",
                "type": "runbook_team",
                "attributes": {"name": "Platform Team"},
                "relationships": {
                    "team": {"data": {"id": "team-100", "type": "team"}},
                },
                "meta": {"users_count": 5},
            },
            {
                "id": "rt-2",
                "type": "runbook_team",
                "attributes": {"name": "DBA Team"},
                "relationships": {
                    "team": {"data": {"id": "team-200", "type": "team"}},
                },
                "meta": {"users_count": 3},
            },
        ],
        "links": {},
    }

    # Call the function
    result = await teams.get_runbook_teams(runbook_id="rb-123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb-123/runbook_teams")

    # Verify the result
    assert len(result) == 2
    assert result[0]["id"] == "rt-1"
    assert result[0]["team_id"] == "team-100"
    assert result[0]["name"] == "Platform Team"
    assert result[0]["users_count"] == 5
    assert result[1]["id"] == "rt-2"
    assert result[1]["team_id"] == "team-200"
    assert result[1]["users_count"] == 3


@pytest.mark.asyncio
async def test_get_runbook_teams_with_pagination(mock_client_manager):
    """Test that teams pagination follows links.next."""
    # Set up mock responses for 2 pages
    mock_client_manager.request.side_effect = [
        {
            "data": [
                {
                    "id": "rt-1",
                    "type": "runbook_team",
                    "attributes": {"name": "Team A"},
                    "relationships": {"team": {"data": {"id": "team-1", "type": "team"}}},
                    "meta": {"users_count": 2},
                },
            ],
            "links": {"next": "core/runbooks/rb-123/runbook_teams?cursor=abc"},
        },
        {
            "data": [
                {
                    "id": "rt-2",
                    "type": "runbook_team",
                    "attributes": {"name": "Team B"},
                    "relationships": {"team": {"data": {"id": "team-2", "type": "team"}}},
                    "meta": {"users_count": 4},
                },
            ],
            "links": {},
        },
    ]

    # Call the function
    result = await teams.get_runbook_teams(runbook_id="rb-123")

    # Verify both pages were fetched
    assert mock_client_manager.request.call_count == 2
    assert len(result) == 2
    assert result[0]["id"] == "rt-1"
    assert result[1]["id"] == "rt-2"


@pytest.mark.asyncio
async def test_get_runbook_teams_missing_team_relationship(mock_client_manager):
    """Test handling when team relationship is missing."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "rt-1",
                "type": "runbook_team",
                "attributes": {"name": "Orphan Team"},
                "relationships": {},
                "meta": {"users_count": 0},
            },
        ],
        "links": {},
    }

    # Call the function
    result = await teams.get_runbook_teams(runbook_id="rb-123")

    # Verify team_id is None when relationship is missing
    assert result[0]["team_id"] is None
    assert result[0]["name"] == "Orphan Team"


@pytest.mark.asyncio
async def test_get_runbook_teams_empty(mock_client_manager):
    """Test fetching teams when runbook has none."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    result = await teams.get_runbook_teams(runbook_id="rb-no-teams")

    # Verify the result is empty
    assert result == []


@pytest.mark.asyncio
async def test_get_runbook_teams_error_handling(mock_client_manager):
    """Test error handling for teams."""
    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Runbook not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await teams.get_runbook_teams(runbook_id="nonexistent")

    assert exc_info.value.response.status_code == 404
