import os
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_env():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    os.environ["CUTOVER_BASE_URL"] = "https://test.cutover.com"
    os.environ["CUTOVER_API_TOKEN"] = "test-token-123"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_api_client():
    """Provide a mocked API client."""
    client = AsyncMock()
    client.request = AsyncMock()
    return client


@pytest.fixture
def mock_client_manager(mock_api_client):
    """Provide a mocked API client manager."""
    with patch("cutover_mcp.clients.api.client_mgr.get_client", return_value=mock_api_client):
        yield mock_api_client
