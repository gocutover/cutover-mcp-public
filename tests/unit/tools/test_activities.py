from unittest.mock import AsyncMock

import httpx
import pytest

from cutover_mcp.tools import activities


@pytest.mark.asyncio
async def test_get_activities_basic(mock_client_manager):
    """Test fetching activities with no filters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "act-123",
                "attributes": {
                    "key": "task.created",
                    "starred": False,
                    "created_at": "2025-01-15T10:00:00Z",
                    "changes": [],
                },
                "relationships": {},
                "meta": {"message": {"plain": "Task created"}},
            }
        ],
        "links": {},
    }

    # Call the function
    result = await activities.get_activities(runbook_id="rb-456")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/activities", params={"runbook_id": "rb-456"})

    # Verify the result
    assert len(result) == 1
    assert result[0]["id"] == "act-123"
    assert result[0]["key"] == "task.created"
    assert result[0]["description"] == "Task created"


@pytest.mark.asyncio
async def test_get_activities_with_date_filters(mock_client_manager):
    """Test activities retrieval with created_after and created_before filters."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    await activities.get_activities(
        runbook_id="rb-789",
        created_after="2025-01-01T00:00:00Z",
        created_before="2025-12-31T23:59:59Z",
    )

    # Verify the API call includes date filters as params
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/activities",
        params={
            "runbook_id": "rb-789",
            "created_after": "2025-01-01T00:00:00Z",
            "created_before": "2025-12-31T23:59:59Z",
        },
    )


@pytest.mark.asyncio
async def test_get_activities_with_pagination(mock_client_manager):
    """Test activities retrieval with multiple pages."""
    # Set up mock responses for 2 pages
    mock_client_manager.request.side_effect = [
        {
            "data": [{"id": "act-1", "attributes": {}, "relationships": {}, "meta": {}}],
            "links": {"next": "https://api.cutover.com/core/activities?runbook_id=rb-100&page[number]=2"},
        },
        {
            "data": [{"id": "act-2", "attributes": {}, "relationships": {}, "meta": {}}],
            "links": {},
        },
    ]

    # Call the function
    result = await activities.get_activities(runbook_id="rb-100")

    # Verify both pages were fetched
    assert len(result) == 2
    assert result[0]["id"] == "act-1"
    assert result[1]["id"] == "act-2"
    assert mock_client_manager.request.call_count == 2
    calls = mock_client_manager.request.call_args_list
    assert calls[0] == (("GET", "core/activities"), {"params": {"runbook_id": "rb-100"}})
    assert calls[1] == (("GET", "https://api.cutover.com/core/activities?runbook_id=rb-100&page[number]=2"), {"params": None})


@pytest.mark.asyncio
async def test_get_activities_with_relationships(mock_client_manager):
    """Test activities with activist, trackable, and recipient relationships."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "act-200",
                "attributes": {"key": "task.updated", "created_at": "2025-01-15T12:00:00Z"},
                "relationships": {
                    "activist": {"data": {"id": "user-1", "type": "user"}},
                    "trackable": {"data": {"id": "task-1", "type": "task"}},
                    "recipient": {"data": {"id": "112", "type": "runbook"}},
                },
                "meta": {},
            }
        ],
        "links": {},
    }

    # Call the function
    result = await activities.get_activities(runbook_id="rb-300")

    # Verify relationships are extracted
    assert result[0]["activist_id"] == "user-1"
    assert result[0]["activist_type"] == "user"
    assert result[0]["trackable_id"] == "task-1"
    assert result[0]["trackable_type"] == "task"
    assert result[0]["recipient_id"] == "112"
    assert result[0]["recipient_type"] == "runbook"


@pytest.mark.asyncio
async def test_get_activities_empty_response(mock_client_manager):
    """Test handling of empty activities response."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    result = await activities.get_activities(runbook_id="rb-404")

    # Verify the result is empty
    assert result == []


@pytest.mark.asyncio
async def test_get_activities_without_meta_message(mock_client_manager):
    """Test activity without meta.message.plain field."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [{"id": "act-500", "attributes": {"key": "comment.added"}, "relationships": {}, "meta": {}}],
        "links": {},
    }

    # Call the function
    result = await activities.get_activities(runbook_id="rb-500")

    # Verify description is not present when meta.message is missing
    assert "description" not in result[0]


@pytest.mark.asyncio
async def test_get_activities_starred(mock_client_manager):
    """Test activity with starred attribute set to True."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "act-600",
                "attributes": {"key": "milestone.reached", "starred": True, "created_at": "2025-01-15T15:00:00Z"},
                "relationships": {},
                "meta": {},
            }
        ],
        "links": {},
    }

    # Call the function
    result = await activities.get_activities(runbook_id="rb-600")

    # Verify starred is True
    assert result[0]["starred"] is True


@pytest.mark.asyncio
async def test_get_activities_error_handling(mock_client_manager):
    """Test error handling for activities."""
    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '403 Forbidden'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await activities.get_activities(runbook_id="rb-forbidden")

    assert exc_info.value.response.status_code == 403
