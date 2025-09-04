from unittest.mock import AsyncMock

import pytest

from cutover_mcp.tools import runbooks


@pytest.mark.asyncio
async def test_get_runbook_by_id(mock_client_manager):
    """Test fetching a specific runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "rb123",
            "type": "runbook",
            "attributes": {
                "name": "Test Runbook",
                "description": "A test runbook",
                "status": "green",
                "is_template": False,
            },
        }
    }

    # Call the function
    result = await runbooks.get_runbook_by_id.fn("rb123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb123")

    # Verify the result
    assert result.data.id == "rb123"
    assert result.data.attributes.name == "Test Runbook"
    assert result.data.attributes.status == "green"


@pytest.mark.asyncio
async def test_list_runbooks(mock_client_manager):
    """Test listing runbooks in a workspace."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "rb1",
                "type": "runbook",
                "attributes": {"name": "Runbook 1"},
            },
            {
                "id": "rb2",
                "type": "runbook",
                "attributes": {"name": "Runbook 2"},
            },
        ],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    # Call the function
    result = await runbooks.list_runbooks.fn("ws123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks", params={"workspace_id": "ws123"})

    # Verify the result
    assert len(result.data) == 2
    assert result.data[0].attributes.name == "Runbook 1"


@pytest.mark.asyncio
async def test_get_runbook_tasks(mock_client_manager):
    """Test fetching tasks for a runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "task1",
                "type": "task",
                "attributes": {"name": "Task 1", "stage": "not_startable"},
            },
            {
                "id": "task2",
                "type": "task",
                "attributes": {"name": "Task 2", "stage": "complete"},
            },
        ],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    # Call the function
    result = await runbooks.get_runbook_tasks.fn("rb123")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb123/tasks")

    # Verify the result
    assert len(result.data) == 2
    assert result.data[0].attributes.name == "Task 1"
    assert result.data[1].attributes.stage == "complete"


@pytest.mark.asyncio
async def test_update_runbook_name_only(mock_client_manager):
    """Test updating only the runbook name."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "rb123",
            "type": "runbook",
            "attributes": {
                "name": "Updated Runbook",
                "description": "Original description",
            },
        }
    }

    # Call the function
    result = await runbooks.update_runbook.fn(runbook_id="rb123", name="Updated Runbook")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123",
        json_data={
            "data": {
                "type": "runbook",
                "id": "rb123",
                "attributes": {"name": "Updated Runbook"},
            }
        },
    )

    # Verify the result
    assert result.data.attributes.name == "Updated Runbook"


@pytest.mark.asyncio
async def test_update_runbook_with_rto_tasks(mock_client_manager):
    """Test updating runbook with RTO task relationships."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "rb123",
            "type": "runbook",
            "attributes": {
                "name": "RTO Runbook",
                "rto": 3600,
            },
            "relationships": {
                "rto_start_task": {"data": {"id": "task1", "type": "task"}},
                "rto_end_task": {"data": {"id": "task2", "type": "task"}},
            },
        }
    }

    # Call the function
    result = await runbooks.update_runbook.fn(
        runbook_id="rb123",
        name="RTO Runbook",
        rto=3600,
        rto_start_task="task1",
        rto_end_task="task2",
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123",
        json_data={
            "data": {
                "type": "runbook",
                "id": "rb123",
                "attributes": {"name": "RTO Runbook", "rto": 3600},
                "relationships": {
                    "rto_start_task": {"data": {"type": "task", "id": "task1"}},
                    "rto_end_task": {"data": {"type": "task", "id": "task2"}},
                },
            }
        },
    )

    # Verify the result
    assert result.data.attributes.rto == 3600


@pytest.mark.asyncio
async def test_create_runbook_minimal(mock_client_manager):
    """Test creating a runbook with minimal parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "new-rb",
            "type": "runbook",
            "attributes": {
                "name": "New Runbook",
                "description": "",
            },
            "relationships": {"workspace": {"data": {"id": "ws123", "type": "workspace"}}},
        }
    }

    # Call the function
    result = await runbooks.create_runbook.fn(workspace_id="ws123", name="New Runbook")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks",
        json_data={
            "data": {
                "type": "runbook",
                "attributes": {"name": "New Runbook", "description": ""},
                "relationships": {"workspace": {"data": {"type": "workspace", "id": "ws123"}}},
            }
        },
    )

    # Verify the result
    assert result.data.id == "new-rb"
    assert result.data.attributes.name == "New Runbook"


@pytest.mark.asyncio
async def test_create_runbook_full_params(mock_client_manager):
    """Test creating a runbook with all parameters."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "full-rb",
            "type": "runbook",
            "attributes": {
                "name": "Full Runbook",
                "description": "Complete runbook",
                "status": "amber",
                "is_template": True,
                "rto": 7200,
                "timezone": "UTC",
            },
            "relationships": {
                "workspace": {"data": {"id": "ws123", "type": "workspace"}},
                "runbook_type": {"data": {"id": "rt123", "type": "runbook_type"}},
            },
        }
    }

    # Call the function with all params
    result = await runbooks.create_runbook.fn(
        workspace_id="ws123",
        name="Full Runbook",
        description="Complete runbook",
        status="amber",
        is_template=True,
        rto=7200,
        timezone="UTC",
        runbook_type_id="rt123",
    )

    # Verify the API call
    expected_payload = {
        "data": {
            "type": "runbook",
            "attributes": {
                "name": "Full Runbook",
                "description": "Complete runbook",
                "status": "amber",
                "is_template": True,
                "rto": 7200,
                "timezone": "UTC",
            },
            "relationships": {
                "workspace": {"data": {"type": "workspace", "id": "ws123"}},
                "runbook_type": {"data": {"type": "runbook_type", "id": "rt123"}},
            },
        }
    }
    mock_client_manager.request.assert_called_once_with("POST", "core/runbooks", json_data=expected_payload)

    # Verify the result
    assert result.data.attributes.is_template is True
    assert result.data.attributes.status == "amber"
    assert result.data.attributes.timezone == "UTC"


@pytest.mark.asyncio
async def test_manage_runbook_start(mock_client_manager):
    """Test starting a runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {"status": "started"}

    # Call the function
    result = await runbooks.manage_runbook.fn(
        runbook_id="rb123",
        action="start",
        comms="on",
        run_type="live",
        rebaseline=True,
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/start",
        json_data={
            "meta": {
                "comms": "on",
                "disable_task_notify": False,
                "run_type": "live",
                "rebaseline": True,
                "shift_fixed_times": False,
                "validation_level": "error",
            }
        },
    )

    # Verify the result
    assert result["status"] == "started"


@pytest.mark.asyncio
async def test_manage_runbook_cancel(mock_client_manager):
    """Test cancelling a runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {"status": "cancelled"}

    # Call the function
    result = await runbooks.manage_runbook.fn(
        runbook_id="rb123",
        action="cancel",
        message="Cancelling due to issue",
        notify=True,
    )

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/cancel",
        json_data={
            "meta": {
                "message": "Cancelling due to issue",
                "notify": True,
            }
        },
    )

    # Verify the result
    assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_manage_runbook_pause(mock_client_manager):
    """Test pausing a runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {"status": "paused"}

    # Call the function
    result = await runbooks.manage_runbook.fn(runbook_id="rb123", action="pause", message="Pausing for review")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123/pause",
        json_data={"meta": {"message": "Pausing for review", "notify": False}},
    )

    # Verify the result
    assert result["status"] == "paused"


@pytest.mark.asyncio
async def test_manage_runbook_resume(mock_client_manager):
    """Test resuming a runbook."""
    # Set up mock response
    mock_client_manager.request.return_value = {"status": "resumed"}

    # Call the function
    result = await runbooks.manage_runbook.fn(runbook_id="rb123", action="resume")

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "PATCH", "core/runbooks/rb123/resume", json_data={"meta": {"notify": False}}
    )

    # Verify the result
    assert result["status"] == "resumed"


@pytest.mark.asyncio
async def test_manage_runbook_invalid_action(mock_client_manager):
    """Test invalid action for manage_runbook."""
    # Should raise ValueError for invalid action
    with pytest.raises(ValueError, match="Invalid action: invalid"):
        await runbooks.manage_runbook.fn(runbook_id="rb123", action="invalid")
    mock_client_manager.request.assert_not_called()


@pytest.mark.asyncio
async def test_runbook_not_found_error(mock_client_manager):
    """Test handling 404 error when runbook not found."""
    import httpx

    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Runbook not found"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '404 Not Found'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await runbooks.get_runbook_by_id.fn("invalid-rb")

    assert exc_info.value.response.status_code == 404
