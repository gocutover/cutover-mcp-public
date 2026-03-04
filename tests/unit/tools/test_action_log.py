from unittest.mock import AsyncMock

import httpx
import pytest

from cutover_mcp.tools import action_log


@pytest.mark.asyncio
async def test_get_action_logs_no_filters(mock_client_manager):
    """Test fetching action logs with no filters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "event": "created",
                    "description": "Runbook created",
                    "changes": {"name": "Test Runbook"},
                    "created_at": "2024-01-01T10:00:00Z",
                },
                "relationships": {},
            },
            {
                "id": "log2",
                "type": "action_log",
                "attributes": {
                    "event": "updated",
                    "description": "Task updated",
                    "changes": {},
                    "created_at": "2024-01-01T11:00:00Z",
                },
                "relationships": {},
            },
        ],
        "links": {},
    }

    # Call the function
    result = await action_log.get_action_logs.fn()

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/action_logs", params={})

    # Verify the result
    assert len(result) == 2
    assert result[0]["id"] == "log1"
    assert result[0]["event"] == "created"
    assert result[0]["description"] == "Runbook created"
    assert result[0]["changes"] == {"name": "Test Runbook"}
    assert result[0]["created_at"] == "2024-01-01T10:00:00Z"
    assert result[1]["id"] == "log2"
    assert result[1]["event"] == "updated"


@pytest.mark.asyncio
async def test_get_action_logs_with_runbook_filter(mock_client_manager):
    """Test fetching action logs filtered by runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    await action_log.get_action_logs.fn(runbook_id="rb123")

    # Verify the API call includes runbook filter as params
    mock_client_manager.request.assert_called_once_with("GET", "core/action_logs", params={"runbook_id": "rb123"})


@pytest.mark.asyncio
async def test_get_action_logs_with_user_filter(mock_client_manager):
    """Test fetching action logs filtered by user."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    await action_log.get_action_logs.fn(user_id="user456")

    # Verify the API call includes user filter as params
    mock_client_manager.request.assert_called_once_with("GET", "core/action_logs", params={"user_id": "user456"})


@pytest.mark.asyncio
async def test_get_action_logs_with_workspace_filter(mock_client_manager):
    """Test fetching action logs filtered by workspace."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    await action_log.get_action_logs.fn(workspace_id="ws789")

    # Verify the API call includes workspace filter as params
    mock_client_manager.request.assert_called_once_with("GET", "core/action_logs", params={"workspace_id": "ws789"})


@pytest.mark.asyncio
async def test_get_action_logs_with_date_range(mock_client_manager):
    """Test fetching action logs with date range filters."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    await action_log.get_action_logs.fn(
        created_after="2024-01-01T10:00:00Z",
        created_before="2024-01-01T11:00:00Z",
    )

    # Verify the API call includes date filters as params
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/action_logs",
        params={"created_after": "2024-01-01T10:00:00Z", "created_before": "2024-01-01T11:00:00Z"},
    )


@pytest.mark.asyncio
async def test_get_action_logs_all_filters(mock_client_manager):
    """Test fetching action logs with all filters applied."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function with all filters
    await action_log.get_action_logs.fn(
        runbook_id="rb123",
        user_id="user456",
        workspace_id="ws789",
        created_after="2024-01-01T10:00:00Z",
        created_before="2024-01-01T11:00:00Z",
    )

    # Verify the API call includes all filters as params
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/action_logs",
        params={
            "runbook_id": "rb123",
            "user_id": "user456",
            "workspace_id": "ws789",
            "created_after": "2024-01-01T10:00:00Z",
            "created_before": "2024-01-01T11:00:00Z",
        },
    )


@pytest.mark.asyncio
async def test_get_action_logs_cursor_pagination(mock_client_manager):
    """Test that cursor-based pagination follows links.next across pages."""
    # Set up mock responses for 3 pages
    mock_client_manager.request.side_effect = [
        {
            "data": [
                {
                    "id": "log1",
                    "type": "action_log",
                    "attributes": {
                        "event": "created",
                        "description": "First",
                        "changes": {},
                        "created_at": "2024-01-01T10:00:00Z",
                    },
                    "relationships": {},
                },
            ],
            "links": {"next": "https://api.cutover.com/core/action_logs?page[number]=2"},
        },
        {
            "data": [
                {
                    "id": "log2",
                    "type": "action_log",
                    "attributes": {
                        "event": "updated",
                        "description": "Second",
                        "changes": {},
                        "created_at": "2024-01-01T11:00:00Z",
                    },
                    "relationships": {},
                },
            ],
            "links": {"next": "https://api.cutover.com/core/action_logs?page[number]=3"},
        },
        {
            "data": [
                {
                    "id": "log3",
                    "type": "action_log",
                    "attributes": {
                        "event": "started",
                        "description": "Third",
                        "changes": {},
                        "created_at": "2024-01-01T12:00:00Z",
                    },
                    "relationships": {},
                },
            ],
            "links": {},
        },
    ]

    # Call the function
    result = await action_log.get_action_logs.fn()

    # Verify all pages were fetched
    assert mock_client_manager.request.call_count == 3
    calls = mock_client_manager.request.call_args_list
    assert calls[0] == (("GET", "core/action_logs"), {"params": {}})
    assert calls[1] == (("GET", "https://api.cutover.com/core/action_logs?page[number]=2"), {"params": None})
    assert calls[2] == (("GET", "https://api.cutover.com/core/action_logs?page[number]=3"), {"params": None})

    # Verify all results were aggregated
    assert len(result) == 3
    assert result[0]["id"] == "log1"
    assert result[1]["id"] == "log2"
    assert result[2]["id"] == "log3"


@pytest.mark.asyncio
async def test_get_action_logs_extracts_author_info(mock_client_manager):
    """Test that author relationship data is extracted into flat fields."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "event": "created",
                    "description": "Log",
                    "changes": {},
                    "created_at": "2024-01-01T10:00:00Z",
                },
                "relationships": {
                    "author": {"data": {"id": "user-1", "type": "user"}},
                },
            },
        ],
        "links": {},
    }

    # Call the function
    result = await action_log.get_action_logs.fn()

    # Verify author info is extracted
    assert result[0]["author_id"] == "user-1"
    assert result[0]["author_type"] == "user"


@pytest.mark.asyncio
async def test_get_action_logs_extracts_resource_info(mock_client_manager):
    """Test that resource relationship data is extracted into flat fields."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "event": "updated",
                    "description": "Log",
                    "changes": {},
                    "created_at": "2024-01-01T10:00:00Z",
                },
                "relationships": {
                    "resource": {"data": {"id": "runbook-1", "type": "runbook"}},
                },
            },
        ],
        "links": {},
    }

    # Call the function
    result = await action_log.get_action_logs.fn()

    # Verify resource info is extracted
    assert result[0]["resource_id"] == "runbook-1"
    assert result[0]["resource_type"] == "runbook"


@pytest.mark.asyncio
async def test_get_action_logs_missing_relationships(mock_client_manager):
    """Test that missing relationships don't add extra keys to the result."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "log1",
                "type": "action_log",
                "attributes": {
                    "event": "created",
                    "description": "Log",
                    "changes": {},
                    "created_at": "2024-01-01T10:00:00Z",
                },
                "relationships": {},
            },
        ],
        "links": {},
    }

    # Call the function
    result = await action_log.get_action_logs.fn()

    # Verify no relationship keys are present
    assert "author_id" not in result[0]
    assert "author_type" not in result[0]
    assert "resource_id" not in result[0]
    assert "resource_type" not in result[0]


@pytest.mark.asyncio
async def test_get_action_logs_empty_result(mock_client_manager):
    """Test handling empty action logs result."""
    # Set up mock response with empty data
    mock_client_manager.request.return_value = {"data": [], "links": {}}

    # Call the function
    result = await action_log.get_action_logs.fn(runbook_id="nonexistent")

    # Verify the result is empty
    assert result == []


@pytest.mark.asyncio
async def test_get_action_logs_error_handling(mock_client_manager):
    """Test error handling for action logs."""
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
