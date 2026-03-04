from unittest.mock import AsyncMock

import httpx
import pytest

from cutover_mcp.tools import users


@pytest.mark.asyncio
async def test_get_user(mock_client_manager):
    """Test fetching a user by ID."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "user-123",
            "type": "user",
            "attributes": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
            },
        },
    }

    # Call the function
    result = await users.get_user.fn(user_id="user-123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/users/user-123")

    # Verify the result
    assert result["id"] == "user-123"
    assert result["email"] == "jane.doe@example.com"
    assert result["full_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_get_user_first_name_only(mock_client_manager):
    """Test user with only first name."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "user-456",
            "type": "user",
            "attributes": {
                "first_name": "Alice",
                "last_name": "",
                "email": "alice@example.com",
            },
        },
    }

    # Call the function
    result = await users.get_user.fn(user_id="user-456")

    # Verify full_name is just the first name
    assert result["full_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_user_falls_back_to_name(mock_client_manager):
    """Test that full_name falls back to name attribute when first/last are empty."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "user-789",
            "type": "user",
            "attributes": {
                "first_name": "",
                "last_name": "",
                "name": "System Bot",
                "email": "bot@example.com",
            },
        },
    }

    # Call the function
    result = await users.get_user.fn(user_id="user-789")

    # Verify full_name falls back to name attribute
    assert result["full_name"] == "System Bot"


@pytest.mark.asyncio
async def test_get_user_missing_name_fields(mock_client_manager):
    """Test user when name fields are missing entirely."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "user-000",
            "type": "user",
            "attributes": {
                "email": "unknown@example.com",
            },
        },
    }

    # Call the function
    result = await users.get_user.fn(user_id="user-000")

    # Verify full_name is empty string when no name fields exist
    assert result["full_name"] == ""
    assert result["email"] == "unknown@example.com"


@pytest.mark.asyncio
async def test_get_user_error_handling(mock_client_manager):
    """Test error handling when user is not found."""
    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "User not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await users.get_user.fn(user_id="nonexistent")

    assert exc_info.value.response.status_code == 404
