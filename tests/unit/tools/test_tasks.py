from unittest.mock import AsyncMock

import httpx
import pytest

from cutover_mcp.models import Assignee
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
    assert result.data.attributes.description == ""
    assert result.data.attributes.stage == "not_startable"


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
                "duration": 3600,
            },
            "relationships": {
                "task_type": {"data": {"id": "tt123", "type": "task_type"}},
                "stream": {"data": {"id": "stream123", "type": "stream"}},
                "predecessors": {"data": [{"id": "pred1", "type": "task"}]},
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
        predecessors=["pred1"],
        duration=3600,
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/tasks",
        json_data={
            "data": {
                "type": "task",
                "attributes": {"name": "Full Task", "description": "Task with all params", "duration": 3600},
                "relationships": {
                    "task_type": {"data": {"id": "tt123", "type": "task_type"}},
                    "stream": {"data": {"id": "stream123", "type": "stream"}},
                    "predecessors": {"data": [{"id": "pred1", "type": "task"}]},
                },
            }
        },
    )

    # Verify the result
    assert result.data.id == "task456"
    assert result.data.attributes.description == "Task with all params"


@pytest.mark.asyncio
async def test_add_task_to_runbook_with_duration(mock_client_manager):
    """Test adding a task with duration."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task789",
            "type": "task",
            "attributes": {
                "name": "Timed Task",
                "description": "",
                "duration": 1800,
            },
        }
    }

    # Call the function
    result = await tasks.add_task_to_runbook.fn(runbook_id="rb123", name="Timed Task", duration=1800)

    # Verify duration is included in the payload
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/tasks",
        json_data={"data": {"type": "task", "attributes": {"name": "Timed Task", "description": "", "duration": 1800}}},
    )

    # Verify the result
    assert result.data.attributes.duration == 1800


@pytest.mark.asyncio
async def test_add_task_to_runbook_with_predecessors(mock_client_manager):
    """Test adding a task with predecessors."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task789",
            "type": "task",
            "attributes": {"name": "Dependent Task", "description": ""},
            "relationships": {
                "predecessors": {"data": [{"id": "pred1", "type": "task"}, {"id": "pred2", "type": "task"}]}
            },
        }
    }

    # Call the function
    await tasks.add_task_to_runbook.fn(runbook_id="rb123", name="Dependent Task", predecessors=["pred1", "pred2"])

    # Verify predecessors are included in the payload
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks/rb123/tasks",
        json_data={
            "data": {
                "type": "task",
                "attributes": {"name": "Dependent Task", "description": ""},
                "relationships": {
                    "predecessors": {"data": [{"id": "pred1", "type": "task"}, {"id": "pred2", "type": "task"}]}
                },
            }
        },
    )


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
async def test_update_runbook_task_with_duration(mock_client_manager):
    """Test updating a task with duration."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Timed Task",
                "duration": 7200,
            },
        }
    }

    # Call the function
    await tasks.update_runbook_task.fn(runbook_id="rb123", task_id="task123", duration=7200)

    # Verify duration is included in the payload
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={"data": {"type": "task", "id": "task123", "attributes": {"duration": 7200}}},
    )


@pytest.mark.asyncio
async def test_update_runbook_task_with_custom_field_values(mock_client_manager):
    """Test updating a task with custom field values."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "task123",
            "type": "task",
            "attributes": {
                "name": "Task with Custom Fields",
            },
        }
    }

    custom_fields = [
        {"name": "Priority", "value": "High"},
        {"custom_field_id": "cf456", "value": ["Option A", "Option B"]},
    ]

    # Call the function
    await tasks.update_runbook_task.fn(runbook_id="rb123", task_id="task123", custom_field_values=custom_fields)

    # Verify custom_field_values is included in the payload
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={
            "data": {
                "type": "task",
                "id": "task123",
                "attributes": {"custom_field_values": custom_fields},
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
                "duration": 900,
            },
            "relationships": {
                "predecessors": {"data": [{"id": "pred1", "type": "task"}]},
                "task_type": {"data": {"id": "tt456", "type": "task_type"}},
                "stream": {"data": {"id": "stream456", "type": "stream"}},
            },
        }
    }

    custom_fields = [{"name": "Status", "value": "Ready"}]

    # Call the function with all params
    await tasks.update_runbook_task.fn(
        runbook_id="rb123",
        task_id="task123",
        name="Fully Updated Task",
        description="New description",
        predecessors=["pred1"],
        task_type_id="tt456",
        stream_id="stream456",
        duration=900,
        custom_field_values=custom_fields,
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={
            "data": {
                "type": "task",
                "id": "task123",
                "attributes": {
                    "name": "Fully Updated Task",
                    "description": "New description",
                    "duration": 900,
                    "custom_field_values": custom_fields,
                },
                "relationships": {
                    "predecessors": {"data": [{"id": "pred1", "type": "task"}]},
                    "task_type": {"data": {"id": "tt456", "type": "task_type"}},
                    "stream": {"data": {"id": "stream456", "type": "stream"}},
                },
            }
        },
    )


@pytest.mark.asyncio
async def test_update_runbook_task_with_assignees(mock_client_manager):
    """Test updating a task with assignees (additive, default behaviour)."""
    mock_client_manager.request.return_value = {
        "data": {"id": "task123", "type": "task", "attributes": {"name": "Task"}}
    }

    assignees = [Assignee(id="user1", type="user"), Assignee(id="team1", type="runbook_team")]

    await tasks.update_runbook_task.fn(runbook_id="rb123", task_id="task123", assignees=assignees)

    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={
            "data": {
                "type": "task",
                "id": "task123",
                "attributes": {},
                "relationships": {
                    "assignees": {"data": [{"id": "user1", "type": "user"}, {"id": "team1", "type": "runbook_team"}]}
                },
            },
            "meta": {"delete_excluded_assignees": False},
        },
    )


@pytest.mark.asyncio
async def test_update_runbook_task_with_assignees_replace(mock_client_manager):
    """Test updating a task with delete_excluded_assignees=True replaces the full list."""
    mock_client_manager.request.return_value = {
        "data": {"id": "task123", "type": "task", "attributes": {"name": "Task"}}
    }

    assignees = [Assignee(id="user2", type="user")]

    await tasks.update_runbook_task.fn(
        runbook_id="rb123",
        task_id="task123",
        assignees=assignees,
        delete_excluded_assignees=True,
    )

    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/tasks/task123",
        json_data={
            "data": {
                "type": "task",
                "id": "task123",
                "attributes": {},
                "relationships": {
                    "assignees": {"data": [{"id": "user2", "type": "user"}]}
                },
            },
            "meta": {"delete_excluded_assignees": True},
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


# --- delete_task tests ---


@pytest.mark.asyncio
async def test_delete_task(mock_client_manager):
    """Test deleting a single task."""
    mock_client_manager.request.return_value = {}

    result = await tasks.delete_task.fn(runbook_id="rb123", task_id="task123")

    mock_client_manager.request.assert_called_once_with("DELETE", "core/runbooks/rb123/tasks/task123")
    assert result == {}


@pytest.mark.asyncio
async def test_delete_task_not_found(mock_client_manager):
    """Test deleting a task that doesn't exist returns 404."""
    import httpx

    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Task not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'", request=AsyncMock(), response=mock_response
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await tasks.delete_task.fn(runbook_id="rb123", task_id="nonexistent")

    assert exc_info.value.response.status_code == 404
