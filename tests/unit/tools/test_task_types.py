from unittest.mock import AsyncMock

import pytest

from cutover_mcp.tools import task_types


@pytest.mark.asyncio
async def test_list_task_types(mock_client_manager):
    """Test listing all task types."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "tt1",
                "type": "task_type",
                "attributes": {
                    "name": "Manual Task",
                    "description": "A task that requires manual execution",
                    "color": "#ff5733",
                },
            },
            {
                "id": "tt2",
                "type": "task_type",
                "attributes": {
                    "name": "Automated Task",
                    "description": "A task that runs automatically",
                    "color": "#33c3ff",
                },
            },
            {
                "id": "tt3",
                "type": "task_type",
                "attributes": {
                    "name": "Approval Task",
                    "description": "A task requiring approval",
                    "color": "#ffaa33",
                },
            },
        ],
        "meta": {"count": 3},
    }

    # Call the function
    result = await task_types.list_task_types.fn()

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/task_types")

    # Verify the result
    assert len(result["data"]) == 3
    assert result["data"][0]["attributes"]["name"] == "Manual Task"
    assert result["data"][1]["attributes"]["name"] == "Automated Task"
    assert result["data"][2]["attributes"]["name"] == "Approval Task"

    # Verify attributes
    assert result["data"][0]["attributes"]["color"] == "#ff5733"
    assert result["data"][1]["attributes"]["description"] == "A task that runs automatically"
    assert result["meta"]["count"] == 3


@pytest.mark.asyncio
async def test_list_task_types_empty(mock_client_manager):
    """Test handling empty task types list."""
    # Set up mock response with empty data
    mock_client_manager.request.return_value = {
        "data": [],
        "meta": {"count": 0},
    }

    # Call the function
    result = await task_types.list_task_types.fn()

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/task_types")

    # Verify the result
    assert len(result["data"]) == 0
    assert result["meta"]["count"] == 0


@pytest.mark.asyncio
async def test_list_task_types_minimal_attributes(mock_client_manager):
    """Test task types with minimal attributes."""
    # Set up mock response with minimal data
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "tt_minimal",
                "type": "task_type",
                "attributes": {
                    "name": "Basic Task Type",
                },
            }
        ],
    }

    # Call the function
    result = await task_types.list_task_types.fn()

    # Verify the result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "tt_minimal"
    assert result["data"][0]["attributes"]["name"] == "Basic Task Type"

    # Verify optional attributes are not required
    assert (
        "description" not in result["data"][0]["attributes"] or result["data"][0]["attributes"]["description"] is None
    )
    assert "color" not in result["data"][0]["attributes"] or result["data"][0]["attributes"]["color"] is None


@pytest.mark.asyncio
async def test_list_task_types_error_handling(mock_client_manager):
    """Test error handling for task types listing."""
    import httpx

    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Server error '500 Internal Server Error'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await task_types.list_task_types.fn()

    assert exc_info.value.response.status_code == 500


@pytest.mark.asyncio
async def test_list_task_types_authentication_error(mock_client_manager):
    """Test authentication error for task types listing."""
    import httpx

    # Set up mock to raise authentication error
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '401 Unauthorized'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await task_types.list_task_types.fn()

    assert exc_info.value.response.status_code == 401


@pytest.mark.asyncio
async def test_list_task_types_large_response(mock_client_manager):
    """Test handling large number of task types."""
    # Set up mock response with large number of task types
    large_data = []
    for i in range(100):
        large_data.append(
            {
                "id": f"tt{i}",
                "type": "task_type",
                "attributes": {
                    "name": f"Task Type {i}",
                    "description": f"Description for task type {i}",
                },
            }
        )

    mock_client_manager.request.return_value = {
        "data": large_data,
        "meta": {"count": 100},
    }

    # Call the function
    result = await task_types.list_task_types.fn()

    # Verify the result
    assert len(result["data"]) == 100
    assert result["data"][0]["attributes"]["name"] == "Task Type 0"
    assert result["data"][99]["attributes"]["name"] == "Task Type 99"
    assert result["meta"]["count"] == 100
