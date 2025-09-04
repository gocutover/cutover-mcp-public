from unittest.mock import AsyncMock

import pytest

from cutover_mcp.tools import streams


@pytest.mark.asyncio
async def test_list_streams_without_forecast(mock_client_manager):
    """Test listing streams without forecast data."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "stream1",
                "type": "stream",
                "attributes": {
                    "name": "Primary Stream",
                    "description": "Main execution stream",
                    "is_primary": True,
                },
            },
            {
                "id": "stream2",
                "type": "stream",
                "attributes": {
                    "name": "Secondary Stream",
                    "is_primary": False,
                },
            },
        ],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    # Call the function
    result = await streams.list_streams.fn(runbook_id="rb123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb123/streams", params={})

    # Verify the result
    assert len(result.data) == 2
    assert result.data[0].attributes.name == "Primary Stream"
    assert result.data[0].attributes.is_primary is True


@pytest.mark.asyncio
async def test_list_streams_with_forecast(mock_client_manager):
    """Test listing streams with forecast data."""
    # Set up mock response with forecast fields
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "stream1",
                "type": "stream",
                "attributes": {
                    "name": "Stream with Forecast",
                    "start_display": "2024-01-01T10:00:00Z",
                    "end_display": "2024-01-01T12:00:00Z",
                },
            }
        ],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    # Call the function with forecast
    result = await streams.list_streams.fn(runbook_id="rb123", forecast=True)

    # Verify the API call includes forecast parameter
    mock_client_manager.request.assert_called_once_with(
        "GET", "core/runbooks/rb123/streams", params={"forecast": "true"}
    )

    # Verify the result
    assert result.data[0].attributes.start_display is not None


@pytest.mark.asyncio
async def test_create_stream_minimal(mock_client_manager):
    """Test creating a stream with minimal parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "new-stream",
            "type": "stream",
            "attributes": {
                "name": "New Stream",
                "description": "",
                "is_primary": False,
            },
        }
    }

    # Call the function
    result = await streams.create_stream.fn(runbook_id="rb123", name="New Stream")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/streams",
        json_data={
            "data": {
                "type": "stream",
                "attributes": {"name": "New Stream"},
            }
        },
    )

    # Verify the result
    assert result.data.id == "new-stream"
    assert result.data.attributes.name == "New Stream"


@pytest.mark.asyncio
async def test_create_stream_with_color_and_description(mock_client_manager):
    """Test creating a stream with color and description."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "colored-stream",
            "type": "stream",
            "attributes": {
                "name": "Colored Stream",
                "description": "A stream with color",
                "color": "#ff5733",
            },
        }
    }

    # Call the function
    result = await streams.create_stream.fn(
        runbook_id="rb123",
        name="Colored Stream",
        description="A stream with color",
        color="#ff5733",
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/streams",
        json_data={
            "data": {
                "type": "stream",
                "attributes": {
                    "name": "Colored Stream",
                    "description": "A stream with color",
                    "color": "#ff5733",
                },
            }
        },
    )

    # Verify the result
    assert result.data.attributes.color == "#ff5733"


@pytest.mark.asyncio
async def test_create_substream(mock_client_manager):
    """Test creating a substream with parent."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "substream1",
            "type": "stream",
            "attributes": {
                "name": "Substream",
                "is_primary": False,
            },
            "relationships": {"parent": {"data": {"id": "parent-stream", "type": "stream"}}},
        }
    }

    # Call the function with parent
    result = await streams.create_stream.fn(runbook_id="rb123", name="Substream", parent_stream_id="parent-stream")

    # Verify the API call includes parent relationship
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/streams",
        json_data={
            "data": {
                "type": "stream",
                "attributes": {"name": "Substream"},
                "relationships": {"parent": {"data": {"id": "parent-stream", "type": "stream"}}},
            }
        },
    )

    # Verify the result has parent relationship
    assert result.data.relationships.parent.data.id == "parent-stream"


@pytest.mark.asyncio
async def test_get_stream(mock_client_manager):
    """Test getting a specific stream."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "stream123",
            "type": "stream",
            "attributes": {
                "name": "Specific Stream",
                "description": "Retrieved stream",
                "tasks_count": 5,
            },
        }
    }

    # Call the function
    result = await streams.get_stream.fn(runbook_id="rb123", stream_id="stream123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb123/streams/stream123")

    # Verify the result
    assert result.data.id == "stream123"
    assert result.data.attributes.tasks_count == 5


@pytest.mark.asyncio
async def test_update_stream_name_only(mock_client_manager):
    """Test updating only the stream name."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "stream123",
            "type": "stream",
            "attributes": {
                "name": "Updated Name",
                "description": "Original description",
            },
        }
    }

    # Call the function
    result = await streams.update_stream.fn(runbook_id="rb123", stream_id="stream123", name="Updated Name")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/streams/stream123",
        json_data={
            "data": {
                "type": "stream",
                "id": "stream123",
                "attributes": {"name": "Updated Name"},
            }
        },
    )

    # Verify the result
    assert result.data.attributes.name == "Updated Name"


@pytest.mark.asyncio
async def test_update_stream_all_fields(mock_client_manager):
    """Test updating all stream fields."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "stream123",
            "type": "stream",
            "attributes": {
                "name": "Fully Updated",
                "description": "New description",
                "color": "#00ff00",
            },
        }
    }

    # Call the function with all params
    result = await streams.update_stream.fn(
        runbook_id="rb123",
        stream_id="stream123",
        name="Fully Updated",
        description="New description",
        color="#00ff00",
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/streams/stream123",
        json_data={
            "data": {
                "type": "stream",
                "id": "stream123",
                "attributes": {
                    "name": "Fully Updated",
                    "description": "New description",
                    "color": "#00ff00",
                },
            }
        },
    )

    # Verify all fields were updated
    assert result.data.attributes.name == "Fully Updated"
    assert result.data.attributes.description == "New description"
    assert result.data.attributes.color == "#00ff00"


@pytest.mark.asyncio
async def test_delete_stream(mock_client_manager):
    """Test deleting a stream."""
    # Set up mock response (empty for delete)
    mock_client_manager.request.return_value = {}

    # Call the function
    result = await streams.delete_stream.fn(runbook_id="rb123", stream_id="stream123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("DELETE", "core/runbooks/rb123/streams/stream123")

    # Verify the result is empty
    assert result == {}


@pytest.mark.asyncio
async def test_stream_not_found_error(mock_client_manager):
    """Test handling 404 error when stream not found."""
    import httpx

    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Stream not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await streams.get_stream.fn("rb123", "invalid-stream")

    assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_empty_stream_list(mock_client_manager):
    """Test handling empty stream list."""
    # Set up mock response with empty data
    mock_client_manager.request.return_value = {"data": [], "meta": {"page": {"number": 1}}, "links": {}}

    # Call the function
    result = await streams.list_streams.fn(runbook_id="rb123")

    # Verify the result
    assert len(result.data) == 0
