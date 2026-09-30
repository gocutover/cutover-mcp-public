from unittest.mock import AsyncMock, call

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


@pytest.mark.asyncio
async def test_get_comments_for_task(mock_client_manager):
    """Test listing the comments attached to one task."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "comment123",
                "type": "comment",
                "attributes": {"content": "Deployment step completed successfully", "featured": False},
                "relationships": {"task": {"data": {"id": "task456", "type": "task"}}},
            },
            {
                "id": "comment124",
                "type": "comment",
                "attributes": {"content": "Smoke tests green", "featured": False},
                "relationships": {"task": {"data": {"id": "task456", "type": "task"}}},
            },
        ],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    # Call the function
    result = await comments.get_comments(runbook_id="rb123", task_id="task456")

    # Verify the API call filters on the task
    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/runbooks/rb123/comments",
        params={"task_id": "task456"},
    )

    # Verify the result
    assert len(result.data) == 2
    assert result.data[0].id == "comment123"
    assert result.data[1].attributes.content == "Smoke tests green"
    assert all(c.relationships.task.data.id == "task456" for c in result.data)


@pytest.mark.asyncio
async def test_get_comments_runbook_level(mock_client_manager):
    """Test listing every comment on a runbook (no task filter)."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "comment789",
                "type": "comment",
                "attributes": {"content": "Runbook kicked off"},
            },
            {
                "id": "comment123",
                "type": "comment",
                "attributes": {"content": "Deployment step completed successfully"},
                "relationships": {"task": {"data": {"id": "task456", "type": "task"}}},
            },
        ],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    # Call the function without a task_id
    result = await comments.get_comments(runbook_id="rb123")

    # Verify no filter is sent
    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb123/comments", params={})

    # Verify the result includes both runbook-level and task comments
    assert len(result.data) == 2
    assert result.data[0].relationships is None
    assert result.data[1].relationships.task.data.id == "task456"


@pytest.mark.asyncio
async def test_get_comments_empty(mock_client_manager):
    """Test a runbook with no comments returns an empty list."""
    mock_client_manager.request.return_value = {"data": [], "meta": {"page": {"number": 1}}, "links": {}}

    result = await comments.get_comments(runbook_id="rb123")

    assert result.data == []


@pytest.mark.asyncio
async def test_get_comments_error_handling(mock_client_manager):
    """Test error handling when the runbook doesn't exist."""
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Runbook not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'", request=AsyncMock(), response=mock_response
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await comments.get_comments(runbook_id="nonexistent")

    assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_get_comments_follows_pagination(mock_client_manager):
    """Test that all pages are fetched and the task filter is only sent on the first request."""
    page_1 = {
        "data": [
            {
                "id": "comment1",
                "type": "comment",
                "attributes": {"content": "first"},
                "relationships": {"task": {"data": {"id": "task456", "type": "task"}}},
            }
        ],
        "meta": {"page": {"number": 1}},
        "links": {
            "self": "core/runbooks/rb123/comments?task_id=task456",
            "next": "core/runbooks/rb123/comments?page=2",
        },
    }
    page_2 = {
        "data": [
            {
                "id": "comment2",
                "type": "comment",
                "attributes": {"content": "second"},
                "relationships": {"task": {"data": {"id": "task456", "type": "task"}}},
            }
        ],
        "meta": {"page": {"number": 2}},
        "links": {"self": "core/runbooks/rb123/comments?page=2", "next": None},
    }
    mock_client_manager.request.side_effect = [page_1, page_2]

    result = await comments.get_comments(runbook_id="rb123", task_id="task456")

    # First call carries the filter; the second follows links.next verbatim with no params
    assert mock_client_manager.request.call_args_list == [
        call("GET", "core/runbooks/rb123/comments", params={"task_id": "task456"}),
        call("GET", "core/runbooks/rb123/comments?page=2", params=None),
    ]

    # Both pages are aggregated in order; meta/links come from the last page
    assert [c.id for c in result.data] == ["comment1", "comment2"]
    assert result.meta.page.number == 2
    assert result.links.next is None
