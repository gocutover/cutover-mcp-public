from unittest.mock import AsyncMock

import pytest

from cutover_mcp.tools import workspaces


@pytest.mark.asyncio
async def test_get_workspace_by_id(mock_client_manager):
    """Test fetching a specific workspace."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "id": "ws123",
        "name": "Test Workspace",
        "description": "A test workspace",
    }

    # Call the function
    result = await workspaces.get_workspace_by_id.fn("ws123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/workspaces/ws123")

    # Verify the result
    assert result["id"] == "ws123"
    assert result["name"] == "Test Workspace"
    assert result["description"] == "A test workspace"


@pytest.mark.asyncio
async def test_query_workspaces(mock_client_manager):
    """Test searching for workspaces by query string."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [{"id": "ws1", "name": "Production"}, {"id": "ws2", "name": "Development"}],
        "meta": {"total": 2},
    }

    # Call the function
    result = await workspaces.query_workspaces.fn("prod")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/workspaces", params={"query": "prod"})

    # Verify the result
    assert len(result["data"]) == 2
    assert result["data"][0]["name"] == "Production"


@pytest.mark.asyncio
async def test_list_workspaces_default_params(mock_client_manager):
    """Test listing workspaces with default parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {"data": [{"id": "ws1"}, {"id": "ws2"}], "meta": {"total": 2}}

    # Call the function with defaults
    result = await workspaces.list_workspaces.fn()

    # Verify the API call with default pagination
    mock_client_manager.request.assert_called_once_with(
        "GET", "core/workspaces", params={"page[limit]": 50, "page[offset]": 0}
    )

    # Verify the result
    assert len(result["data"]) == 2


@pytest.mark.asyncio
async def test_list_workspaces_with_pagination(mock_client_manager):
    """Test listing workspaces with custom pagination parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [{"id": "ws3"}, {"id": "ws4"}],
        "meta": {"total": 10, "limit": 2, "offset": 2},
    }

    # Call the function with custom pagination
    result = await workspaces.list_workspaces.fn(limit=2, offset=2)

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "GET", "core/workspaces", params={"page[limit]": 2, "page[offset]": 2}
    )

    # Verify the result
    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "ws3"


@pytest.mark.asyncio
async def test_create_workspace_minimal(mock_client_manager):
    """Test creating a workspace with minimal parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "ws_new",
            "type": "workspace",
            "attributes": {"name": "New Workspace", "description": "", "key": ""},
        }
    }

    # Call the function with minimal params
    result = await workspaces.create_workspace.fn(name="New Workspace")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/workspaces",
        json_data={
            "data": {"type": "workspace", "attributes": {"name": "New Workspace", "description": "", "key": ""}}
        },
    )

    # Verify the result
    assert result["data"]["id"] == "ws_new"
    assert result["data"]["attributes"]["name"] == "New Workspace"


@pytest.mark.asyncio
async def test_create_workspace_full_params(mock_client_manager):
    """Test creating a workspace with all parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "ws_full",
            "type": "workspace",
            "attributes": {"name": "Full Workspace", "description": "A complete workspace", "key": "FULL"},
        }
    }

    # Call the function with all params
    result = await workspaces.create_workspace.fn(name="Full Workspace", description="A complete workspace", key="FULL")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/workspaces",
        json_data={
            "data": {
                "type": "workspace",
                "attributes": {"name": "Full Workspace", "description": "A complete workspace", "key": "FULL"},
            }
        },
    )

    # Verify the result
    assert result["data"]["attributes"]["key"] == "FULL"
    assert result["data"]["attributes"]["description"] == "A complete workspace"


@pytest.mark.asyncio
async def test_workspace_not_found_error(mock_client_manager):
    """Test handling 404 error when workspace not found."""
    # Import the actual httpx exception for more realistic testing
    import httpx

    # Set up mock to raise an HTTPStatusError
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Workspace not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found' for url 'https://test.cutover.com/core/workspaces/invalid'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Call should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await workspaces.get_workspace_by_id.fn("invalid")

    # Verify the exception details
    assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_empty_workspace_list(mock_client_manager):
    """Test handling empty workspace list."""
    # Set up mock response with empty data
    mock_client_manager.request.return_value = {"data": [], "meta": {"total": 0}}

    # Call the function
    result = await workspaces.list_workspaces.fn()

    # Verify the result
    assert result["data"] == []
    assert result["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_query_workspaces_special_characters(mock_client_manager):
    """Test querying workspaces with special characters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [{"id": "ws1", "name": "Test & Development"}],
        "meta": {"total": 1},
    }

    # Call with special characters
    result = await workspaces.query_workspaces.fn("Test & Dev")

    # Verify the API call properly passes the query
    mock_client_manager.request.assert_called_once_with("GET", "core/workspaces", params={"query": "Test & Dev"})

    # Verify the result
    assert len(result["data"]) == 1
    assert result["data"][0]["name"] == "Test & Development"
