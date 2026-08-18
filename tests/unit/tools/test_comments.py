from unittest.mock import AsyncMock

import httpx
import pytest

from cutover_mcp.tools import comments


@pytest.mark.asyncio
async def test_add_comment_on_task(mock_client_manager):
    """Test posting a comment attached to a task."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "comment123",
            "type": "comment",
            "attributes": {
                "content": "Deployment step completed successfully",
                "featured": False,
            },
            "relationships": {
                "task": {"data": {"id": "task456", "type": "task"}},
            },
        }
    }

    # Call the function
    result = await comments.add_comment(
        runbook_id="rb123",
        content="Deployment step completed successfully",
        task_id="task456",
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/comments",
        json_data={
            "data": {
                "type": "comment",
                "attributes": {"content": "Deployment step completed successfully"},
                "relationships": {"task": {"data": {"id": "task456", "type": "task"}}},
            }
        },
    )

    # Verify the result
    assert result.data.id == "comment123"
    assert result.data.attributes.content == "Deployment step completed successfully"
    assert result.data.relationships.task.data.id == "task456"


@pytest.mark.asyncio
async def test_add_comment_runbook_level(mock_client_manager):
    """Test posting a runbook-level comment (no task)."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "comment789",
            "type": "comment",
            "attributes": {
                "content": "Runbook kicked off",
            },
        }
    }

    # Call the function without a task_id
    result = await comments.add_comment(runbook_id="rb123", content="Runbook kicked off")

    # Verify no task relationship is sent
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/comments",
        json_data={"data": {"type": "comment", "attributes": {"content": "Runbook kicked off"}}},
    )

    # Verify the result
    assert result.data.id == "comment789"
    assert result.data.attributes.content == "Runbook kicked off"
    assert result.data.relationships is None


@pytest.mark.asyncio
async def test_add_comment_error_handling(mock_client_manager):
    """Test error handling when the runbook or task doesn't exist."""
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Runbook not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'", request=AsyncMock(), response=mock_response
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await comments.add_comment(runbook_id="nonexistent", content="hello", task_id="task1")

    assert exc_info.value.response.status_code == 404
