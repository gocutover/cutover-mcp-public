from unittest.mock import AsyncMock

import httpx
import pytest

from cutover_mcp.tools import custom_fields


@pytest.mark.asyncio
async def test_list_custom_fields_no_filter(mock_client_manager):
    """Test fetching custom fields without workspace filter."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "cf-1",
                "type": "custom_field",
                "attributes": {
                    "name": "Priority",
                    "field_type": "single_select",
                    "field_options": ["High", "Medium", "Low"],
                    "required": True,
                    "apply_to": "task",
                    "allow_field_creation": False,
                    "default_value": "Medium",
                    "display_name": "Task Priority",
                },
            },
            {
                "id": "cf-2",
                "type": "custom_field",
                "attributes": {
                    "name": "Region",
                    "field_type": "multi_select",
                    "field_options": ["EU", "US", "APAC"],
                    "required": False,
                    "apply_to": "runbook",
                    "allow_field_creation": True,
                    "default_value": None,
                    "display_name": "Region",
                },
            },
        ],
    }

    # Call the function
    result = await custom_fields.list_custom_fields.fn()

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/custom_fields", params={})

    # Verify the result
    assert len(result) == 2
    assert result[0]["id"] == "cf-1"
    assert result[0]["name"] == "Priority"
    assert result[0]["field_type"] == "single_select"
    assert result[0]["field_options"] == ["High", "Medium", "Low"]
    assert result[0]["required"] is True
    assert result[0]["apply_to"] == "task"
    assert result[0]["default_value"] == "Medium"
    assert result[0]["display_name"] == "Task Priority"
    assert result[1]["id"] == "cf-2"
    assert result[1]["allow_field_creation"] is True


@pytest.mark.asyncio
async def test_list_custom_fields_with_workspace_filter(mock_client_manager):
    """Test listing custom fields filtered by workspace."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "cf-1",
                "type": "custom_field",
                "attributes": {
                    "name": "Status",
                    "field_type": "text",
                },
            },
        ],
    }

    # Call the function
    await custom_fields.list_custom_fields.fn(workspace_id="ws-123")

    # Verify the API call includes workspace filter
    mock_client_manager.request.assert_called_once_with("GET", "core/custom_fields", params={"workspace_id": "ws-123"})


@pytest.mark.asyncio
async def test_list_custom_fields_skips_archived(mock_client_manager):
    """Test that archived custom fields are excluded."""
    # Set up mock response with one active and one archived field
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "cf-active",
                "type": "custom_field",
                "attributes": {
                    "name": "Active Field",
                    "field_type": "text",
                    "archived": False,
                },
            },
            {
                "id": "cf-archived",
                "type": "custom_field",
                "attributes": {
                    "name": "Archived Field",
                    "field_type": "text",
                    "archived": True,
                },
            },
        ],
    }

    # Call the function
    result = await custom_fields.list_custom_fields.fn()

    # Verify only the active field is returned
    assert len(result) == 1
    assert result[0]["id"] == "cf-active"


@pytest.mark.asyncio
async def test_list_custom_fields_paginates(mock_client_manager):
    """Test that list_custom_fields fetches all pages when links.next is present."""
    page1 = {
        "data": [
            {
                "id": "cf-1",
                "type": "custom_field",
                "attributes": {
                    "name": "Priority",
                    "field_type": "text",
                    "archived": False,
                },
            },
        ],
        "links": {
            "next": "https://api.cutover.com/core/custom_fields?page[number]=2",
        },
    }
    page2 = {
        "data": [
            {
                "id": "cf-2",
                "type": "custom_field",
                "attributes": {
                    "name": "Region",
                    "field_type": "text",
                    "archived": False,
                },
            },
        ],
        "links": {},
    }
    mock_client_manager.request.side_effect = [page1, page2]

    result = await custom_fields.list_custom_fields.fn()

    assert len(result) == 2
    assert result[0]["id"] == "cf-1"
    assert result[1]["id"] == "cf-2"
    assert mock_client_manager.request.call_count == 2
    mock_client_manager.request.assert_any_call(
        "GET",
        "https://api.cutover.com/core/custom_fields?page[number]=2",
        params=None,
    )


@pytest.mark.asyncio
async def test_list_custom_fields_empty(mock_client_manager):
    """Test listing custom fields when none exist."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": []}

    # Call the function
    result = await custom_fields.list_custom_fields.fn()

    # Verify the result is empty
    assert result == []


@pytest.mark.asyncio
async def test_get_custom_field(mock_client_manager):
    """Test fetching a single custom field by ID."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "cf-1",
            "type": "custom_field",
            "attributes": {
                "name": "Environment",
                "field_type": "single_select",
                "field_options": ["Production", "Staging", "Dev"],
                "required": True,
                "apply_to": "runbook",
                "allow_field_creation": False,
                "default_value": "Dev",
                "display_name": "Environment",
            },
        },
    }

    # Call the function
    result = await custom_fields.get_custom_field.fn(custom_field_id="cf-1")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/custom_fields/cf-1")

    # Verify the result
    assert result["id"] == "cf-1"
    assert result["name"] == "Environment"
    assert result["field_type"] == "single_select"
    assert result["field_options"] == ["Production", "Staging", "Dev"]
    assert result["required"] is True
    assert result["apply_to"] == "runbook"
    assert result["allow_field_creation"] is False
    assert result["default_value"] == "Dev"
    assert result["display_name"] == "Environment"


@pytest.mark.asyncio
async def test_get_custom_field_error_handling(mock_client_manager):
    """Test error handling when custom field is not found."""
    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await custom_fields.get_custom_field.fn(custom_field_id="nonexistent")

    assert exc_info.value.response.status_code == 404
