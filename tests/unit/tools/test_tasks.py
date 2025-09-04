from unittest.mock import AsyncMock

import pytest

from cutover_mcp.tools import tasks


@pytest.mark.asyncio
async def test_add_task_to_runbook_minimal(mock_client_manager):
    """Test adding a task with minimal parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "New Task",
                "description": "",
                "stage": "not_startable",
            },
        }
    }

    # Call the function
    result = await tasks.add_task_to_runbook.fn(runbook_id="rb123", name="New Task")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/tasks",
        json_data={"data": {"type": "task", "attributes": {"name": "New Task", "description": ""}}},
    )

    # Verify the result
    assert result.data.id == "task123"
    assert result.data.attributes.name == "New Task"


@pytest.mark.asyncio
async def test_add_task_to_runbook_full_params(mock_client_manager):
    """Test adding a task with all parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task456",
            "type": "task",
            "attributes": {
                "name": "Full Task",
                "description": "Task with all params",
                "stage": "not_startable",
            },
            "relationships": {
                "task_type": {"data": {"id": "tt123", "type": "task_type"}},
                "stream": {"data": {"id": "stream123", "type": "stream"}},
            },
        }
    }

    # Call the function with all params
    result = await tasks.add_task_to_runbook.fn(
        runbook_id="rb123",
        name="Full Task",
        description="Task with all params",
        task_type_id="tt123",
        stream_id="stream123",
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/tasks",
        json_data={
            "data": {
                "type": "task",
                "attributes": {"name": "Full Task", "description": "Task with all params"},
                "relationships": {
                    "task_type": {"data": {"id": "tt123", "type": "task_type"}},
                    "stream": {"data": {"id": "stream123", "type": "stream"}},
                },
            }
        },
    )

    # Verify the result
    assert result.data.id == "task456"
    assert result.data.attributes.description == "Task with all params"


@pytest.mark.asyncio
async def test_update_runbook_task_name_only(mock_client_manager):
    """Test updating a task with only name."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Updated Task Name",
                "description": "Original description",
            },
        }
    }

    # Call the function
    result = await tasks.update_runbook_task.fn(runbook_id="rb123", task_id="task123", name="Updated Task Name")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={"data": {"type": "task", "id": "task123", "attributes": {"name": "Updated Task Name"}}},
    )

    # Verify the result
    assert result.data.attributes.name == "Updated Task Name"


@pytest.mark.asyncio
async def test_update_runbook_task_with_predecessors(mock_client_manager):
    """Test updating a task with predecessors."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Task with Dependencies",
            },
            "relationships": {
                "predecessors": {"data": [{"id": "pred1", "type": "task"}, {"id": "pred2", "type": "task"}]}
            },
        }
    }

    # Call the function
    await tasks.update_runbook_task.fn(runbook_id="rb123", task_id="task123", predecessors=["pred1", "pred2"])

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={
            "data": {
                "type": "task",
                "id": "task123",
                "attributes": {},
                "relationships": {
                    "predecessors": {"data": [{"id": "pred1", "type": "task"}, {"id": "pred2", "type": "task"}]}
                },
            }
        },
    )


@pytest.mark.asyncio
async def test_update_runbook_task_all_params(mock_client_manager):
    """Test updating a task with all parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Fully Updated Task",
                "description": "New description",
            },
            "relationships": {
                "predecessors": {"data": [{"id": "pred1", "type": "task"}]},
                "task_type": {"data": {"id": "tt456", "type": "task_type"}},
                "stream": {"data": {"id": "stream456", "type": "stream"}},
            },
        }
    }

    # Call the function with all params
    await tasks.update_runbook_task.fn(
        runbook_id="rb123",
        task_id="task123",
        name="Fully Updated Task",
        description="New description",
        predecessors=["pred1"],
        task_type_id="tt456",
        stream_id="stream456",
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={
            "data": {
                "type": "task",
                "id": "task123",
                "attributes": {"name": "Fully Updated Task", "description": "New description"},
                "relationships": {
                    "predecessors": {"data": [{"id": "pred1", "type": "task"}]},
                    "task_type": {"data": {"id": "tt456", "type": "task_type"}},
                    "stream": {"data": {"id": "stream456", "type": "stream"}},
                },
            }
        },
    )


@pytest.mark.asyncio
async def test_start_task(mock_client_manager):
    """Test starting a task."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Started Task",
                "stage": "in_progress",
            },
        }
    }

    # Call the function
    result = await tasks.start_task.fn(runbook_id="rb123", task_id="task123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("PATCH", "core/runbooks/rb123/tasks/task123/start")

    # Verify the result
    assert result.data.attributes.stage == "in_progress"


@pytest.mark.asyncio
async def test_complete_task(mock_client_manager):
    """Test completing a task."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Completed Task",
                "stage": "complete",
            },
        }
    }

    # Call the function
    result = await tasks.complete_task.fn(runbook_id="rb123", task_id="task123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("PATCH", "core/runbooks/rb123/tasks/task123/finish")

    # Verify the result
    assert result.data.attributes.stage == "complete"


@pytest.mark.asyncio
async def test_skip_task(mock_client_manager):
    """Test skipping a task."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Skipped Task",
                "stage": "complete",
            },
        }
    }

    # Call the function
    result = await tasks.skip_task.fn(runbook_id="rb123", task_id="task123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("PATCH", "core/runbooks/rb123/tasks/task123/skip")

    # Verify the result
    assert result.data.id == "task123"


@pytest.mark.asyncio
async def test_task_error_handling(mock_client_manager):
    """Test error handling for task operations."""
    import httpx

    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Task not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'", request=AsyncMock(), response=mock_response
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await tasks.start_task.fn("rb123", "invalid-task")

    assert exc_info.value.response.status_code == 404
