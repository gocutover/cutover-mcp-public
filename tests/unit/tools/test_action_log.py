from unittest.mock import AsyncMock

import pytest

from cutover_mcp.tools import action_log


@pytest.mark.asyncio
async def test_get_action_logs_minimal(mock_client_manager):
    """Test getting action logs with minimal parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "action": "task_started",
                    "created_at": "2024-01-01T10:00:00Z",
                    "details": {"task_name": "Test Task"},
                },
            },
            {
                "id": "log2",
                "type": "action_log",
                "attributes": {
                    "action": "runbook_started",
                    "created_at": "2024-01-01T09:00:00Z",
                    "details": {"runbook_name": "Test Runbook"},
                },
            },
        ],
        "meta": {"pagination": {"page": 1, "pages": 1, "count": 2}},
    }

    # Call the function with defaults
    result = await action_log.get_action_logs.fn()

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "GET", "core/action_logs", params={"page[number]": 1, "page[size]": 50}
    )

    # Verify the result
    assert len(result["data"]) == 2
    assert result["data"][0]["attributes"]["action"] == "task_started"
    assert result["meta"]["pagination"]["count"] == 2


@pytest.mark.asyncio
async def test_get_action_logs_with_runbook_filter(mock_client_manager):
    """Test getting action logs filtered by runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "action": "task_completed",
                    "created_at": "2024-01-01T11:00:00Z",
                },
            }
        ],
        "meta": {"pagination": {"page": 1, "pages": 1, "count": 1}},
    }

    # Call the function with runbook filter
    result = await action_log.get_action_logs.fn(runbook_id="rb123")

    # Verify the API call includes runbook filter
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/action_logs",
        params={"page[number]": 1, "page[size]": 50, "runbook_id": "rb123"},
    )

    # Verify the result
    assert len(result["data"]) == 1
    assert result["data"][0]["attributes"]["action"] == "task_completed"


@pytest.mark.asyncio
async def test_get_action_logs_with_user_filter(mock_client_manager):
    """Test getting action logs filtered by user."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "action": "comment_added",
                    "created_at": "2024-01-01T12:00:00Z",
                },
            }
        ],
    }

    # Call the function with user filter
    result = await action_log.get_action_logs.fn(user_id="user123")

    # Verify the API call includes user filter
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/action_logs",
        params={"page[number]": 1, "page[size]": 50, "user_id": "user123"},
    )

    # Verify the result
    assert result["data"][0]["attributes"]["action"] == "comment_added"


@pytest.mark.asyncio
async def test_get_action_logs_with_workspace_filter(mock_client_manager):
    """Test getting action logs filtered by workspace."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "action": "workspace_updated",
                    "created_at": "2024-01-01T13:00:00Z",
                },
            }
        ],
    }

    # Call the function with workspace filter
    result = await action_log.get_action_logs.fn(workspace_id="ws123")

    # Verify the API call includes workspace filter
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/action_logs",
        params={"page[number]": 1, "page[size]": 50, "workspace_id": "ws123"},
    )

    # Verify the result
    assert result["data"][0]["attributes"]["action"] == "workspace_updated"


@pytest.mark.asyncio
async def test_get_action_logs_with_date_range(mock_client_manager):
    """Test getting action logs with date range filters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "action": "task_started",
                    "created_at": "2024-01-01T10:30:00Z",
                },
            }
        ],
    }

    # Call the function with date range
    result = await action_log.get_action_logs.fn(
        created_after="2024-01-01T10:00:00Z", created_before="2024-01-01T11:00:00Z"
    )

    # Verify the API call includes date filters
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/action_logs",
        params={
            "page[number]": 1,
            "page[size]": 50,
            "created_after": "2024-01-01T10:00:00Z",
            "created_before": "2024-01-01T11:00:00Z",
        },
    )

    # Verify the result
    assert result["data"][0]["attributes"]["created_at"] == "2024-01-01T10:30:00Z"


@pytest.mark.asyncio
async def test_get_action_logs_with_pagination(mock_client_manager):
    """Test getting action logs with custom pagination."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log11",
                "type": "action_log",
                "attributes": {"action": "page_2_log"},
            }
        ],
        "meta": {"pagination": {"page": 2, "pages": 5, "count": 100}},
    }

    # Call the function with custom pagination
    result = await action_log.get_action_logs.fn(page_number=2, page_size=20)

    # Verify the API call includes pagination
    mock_client_manager.request.assert_called_once_with(
        "GET", "core/action_logs", params={"page[number]": 2, "page[size]": 20}
    )

    # Verify the result
    assert result["meta"]["pagination"]["page"] == 2
    assert result["data"][0]["attributes"]["action"] == "page_2_log"


@pytest.mark.asyncio
async def test_get_action_logs_all_filters(mock_client_manager):
    """Test getting action logs with all filters applied."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "filtered-log",
                "type": "action_log",
                "attributes": {
                    "action": "specific_action",
                    "created_at": "2024-01-01T10:15:00Z",
                },
            }
        ],
    }

    # Call the function with all filters
    result = await action_log.get_action_logs.fn(
        runbook_id="rb123",
        user_id="user456",
        workspace_id="ws789",
        created_after="2024-01-01T10:00:00Z",
        created_before="2024-01-01T11:00:00Z",
        page_number=3,
        page_size=25,
    )

    # Verify the API call includes all filters
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/action_logs",
        params={
            "page[number]": 3,
            "page[size]": 25,
            "runbook_id": "rb123",
            "user_id": "user456",
            "workspace_id": "ws789",
            "created_after": "2024-01-01T10:00:00Z",
            "created_before": "2024-01-01T11:00:00Z",
        },
    )

    # Verify the result
    assert result["data"][0]["id"] == "filtered-log"


@pytest.mark.asyncio
async def test_get_action_logs_empty_result(mock_client_manager):
    """Test handling empty action logs result."""
    # Set up mock response with empty data
    mock_client_manager.request.return_value = {
        "data": [],
        "meta": {"pagination": {"page": 1, "pages": 0, "count": 0}},
    }

    # Call the function
    result = await action_log.get_action_logs.fn(runbook_id="nonexistent")

    # Verify the result is empty
    assert len(result["data"]) == 0
    assert result["meta"]["pagination"]["count"] == 0


@pytest.mark.asyncio
async def test_get_action_logs_error_handling(mock_client_manager):
    """Test error handling for action logs."""
    import httpx

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
        await action_log.get_action_logs.fn()

    assert exc_info.value.response.status_code == 403
