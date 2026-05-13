from unittest.mock import AsyncMock

import httpx
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
async def test_list_runbooks_with_filters(mock_client_manager):
    """Test listing runbooks with source_runbook_id and folder_id filters."""
    mock_client_manager.request.return_value = {
        "data": [{"id": "rb1", "type": "runbook", "attributes": {"name": "Runbook 1"}}],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    result = await runbooks.list_runbooks.fn("ws123", source_runbook_id="tmpl1", folder_id="f42")

    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/runbooks",
        params={"workspace_id": "ws123", "source_runbook_id": "tmpl1", "folder_id": "f42"},
    )
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_list_runbooks_with_is_template_false(mock_client_manager):
    """Test that is_template=False is serialized as lowercase 'false'."""
    mock_client_manager.request.return_value = {
        "data": [],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    await runbooks.list_runbooks.fn("ws123", is_template=False)

    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/runbooks",
        params={"workspace_id": "ws123", "is_template": "false"},
    )


@pytest.mark.asyncio
async def test_list_runbooks_with_pagination(mock_client_manager):
    """Test that list_runbooks fetches all pages."""
    mock_client_manager.request.side_effect = [
        {
            "data": [{"id": "rb1", "type": "runbook", "attributes": {"name": "Runbook 1"}}],
            "links": {"next": "core/runbooks?workspace_id=ws123&cursor=abc"},
        },
        {
            "data": [{"id": "rb2", "type": "runbook", "attributes": {"name": "Runbook 2"}}],
            "links": {},
        },
    ]

    result = await runbooks.list_runbooks.fn("ws123")

    assert mock_client_manager.request.call_count == 2
    calls = mock_client_manager.request.call_args_list
    assert calls[0] == (("GET", "core/runbooks"), {"params": {"workspace_id": "ws123"}})
    assert calls[1] == (("GET", "core/runbooks?workspace_id=ws123&cursor=abc"), {"params": None})
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_get_runbook_tasks(mock_client_manager):
    """Test fetching tasks for a runbook with no filters."""
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

    result = await runbooks.get_runbook_tasks.fn("rb123")

    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb123/tasks", params={})

    assert len(result.data) == 2
    assert result.data[0].attributes.name == "Task 1"
    assert result.data[1].attributes.stage == "complete"


@pytest.mark.asyncio
async def test_get_runbook_tasks_with_stage_filter(mock_client_manager):
    """Test fetching tasks filtered by stage."""
    mock_client_manager.request.return_value = {
        "data": [{"id": "task1", "type": "task", "attributes": {"name": "Task 1", "stage": "in_progress"}}],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    result = await runbooks.get_runbook_tasks.fn("rb123", stage=["in_progress"])

    mock_client_manager.request.assert_called_once_with(
        "GET", "core/runbooks/rb123/tasks", params={"stage": "in_progress"}
    )
    assert len(result.data) == 1
    assert result.data[0].attributes.stage == "in_progress"


@pytest.mark.asyncio
async def test_get_runbook_tasks_with_multiple_filters(mock_client_manager):
    """Test fetching tasks with multiple filters combined."""
    mock_client_manager.request.return_value = {
        "data": [{"id": "task1", "type": "task", "attributes": {"name": "Deploy"}}],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    result = await runbooks.get_runbook_tasks.fn(
        "rb123",
        stage=["startable", "in_progress"],
        stream_id=["stream1"],
        search_term="Deploy",
    )

    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/runbooks/rb123/tasks",
        params={"stage": "startable,in_progress", "stream_id": "stream1", "search_term": "Deploy"},
    )
    assert result.data[0].attributes.name == "Deploy"


@pytest.mark.asyncio
async def test_get_runbook_tasks_with_forecast(mock_client_manager):
    """Test fetching tasks in forecast mode."""
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "task1",
                "type": "task",
                "attributes": {
                    "name": "Task 1",
                    "start_display": "2026-04-01T10:00:00Z",
                    "end_display": "2026-04-01T11:00:00Z",
                },
            }
        ],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    result = await runbooks.get_runbook_tasks.fn("rb123", forecast=True)

    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks/rb123/tasks", params={"forecast": "true"})
    assert len(result.data) == 1
    assert result.data[0].attributes.start_display is not None
    assert result.data[0].attributes.end_display is not None


@pytest.mark.asyncio
async def test_get_runbook_tasks_pagination(mock_client_manager):
    """Test that get_runbook_tasks follows pagination and returns all tasks."""
    mock_client_manager.request.side_effect = [
        {
            "data": [{"id": "task1", "type": "task", "attributes": {"name": "Task 1"}}],
            "meta": {"page": {"number": 1}},
            "links": {"next": "core/runbooks/rb123/tasks?page[number]=2"},
        },
        {
            "data": [{"id": "task2", "type": "task", "attributes": {"name": "Task 2"}}],
            "meta": {"page": {"number": 2}},
            "links": {},
        },
    ]

    result = await runbooks.get_runbook_tasks.fn("rb123")

    assert mock_client_manager.request.call_count == 2
    calls = mock_client_manager.request.call_args_list
    assert calls[0] == (("GET", "core/runbooks/rb123/tasks"), {"params": {}})
    assert calls[1] == (("GET", "core/runbooks/rb123/tasks?page[number]=2"), {"params": None})
    assert len(result.data) == 2
    assert result.data[0].id == "task1"
    assert result.data[1].id == "task2"


@pytest.mark.asyncio
async def test_get_runbook_tasks_with_fields_task(mock_client_manager):
    """Test that fields_task list is joined into a comma-separated string for the API."""
    mock_client_manager.request.return_value = {
        "data": [{"id": "1", "type": "task", "attributes": {"name": "Task 1", "stage": "startable"}}],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    await runbooks.get_runbook_tasks.fn("rb123", fields_task=["name", "stage", "start_planned"])

    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/runbooks/rb123/tasks",
        params={"fields[task]": "name,stage,start_planned"},
    )


@pytest.mark.asyncio
async def test_get_runbook_tasks_with_completion_type_level_has_comments_and_sort(mock_client_manager):
    """Test filtering by completion_type, level, has_comments, and sort order."""
    mock_client_manager.request.return_value = {
        "data": [],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    await runbooks.get_runbook_tasks.fn(
        "rb123",
        completion_type="complete_normal",
        level="1",
        has_comments=True,
        sort="-start_planned",
    )

    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/runbooks/rb123/tasks",
        params={
            "completion_type": "complete_normal",
            "level": "1",
            "has_comments": "true",
            "sort": "-start_planned",
        },
    )


@pytest.mark.asyncio
async def test_get_runbook_tasks_with_task_type_team_user_and_source_filters(mock_client_manager):
    """Test filtering by task_type_id, runbook_team_id, user_id, and source_runbook_id."""
    mock_client_manager.request.return_value = {
        "data": [],
        "meta": {"page": {"number": 1}},
        "links": {},
    }

    await runbooks.get_runbook_tasks.fn(
        "rb123",
        task_type_id=["tt1", "tt2"],
        runbook_team_id=["team1"],
        user_id=["u1", "u2"],
        source_runbook_id=["rb-template"],
    )

    mock_client_manager.request.assert_called_once_with(
        "GET",
        "core/runbooks/rb123/tasks",
        params={
            "task_type_id": "tt1,tt2",
            "runbook_team_id": "team1",
            "user_id": "u1,u2",
            "source_runbook_id": "rb-template",
        },
    )


@pytest.mark.asyncio
async def test_get_runbook_tasks_forecast_does_not_paginate(mock_client_manager):
    """Test that forecast mode makes exactly one request regardless of links."""
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "1",
                "type": "task",
                "attributes": {"start_display": "2026-04-01T10:00:00Z", "end_display": "2026-04-01T11:00:00Z"},
            },
            {
                "id": "2",
                "type": "task",
                "attributes": {"start_display": "2026-04-01T11:00:00Z", "end_display": "2026-04-01T12:00:00Z"},
            },
        ],
        "meta": {"page": {"number": 1, "total": None}},
        "links": {"next": "core/runbooks/rb123/tasks?page[number]=2"},
    }

    result = await runbooks.get_runbook_tasks.fn("rb123", forecast=True)

    mock_client_manager.request.assert_called_once()
    assert len(result.data) == 2


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
async def test_create_runbook_with_template_type(mock_client_manager):
    """Test creating a runbook with template_type set to default."""
    mock_client_manager.request.return_value = {
        "data": {
            "id": "tmpl-rb",
            "type": "runbook",
            "attributes": {
                "name": "My Template",
                "description": "",
                "template_type": "default",
                "is_template": True,
            },
            "relationships": {"workspace": {"data": {"id": "ws123", "type": "workspace"}}},
        }
    }

    result = await runbooks.create_runbook.fn(
        workspace_id="ws123",
        name="My Template",
        template_type="default",
    )

    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/runbooks",
        json_data={
            "data": {
                "type": "runbook",
                "attributes": {"name": "My Template", "description": "", "template_type": "default"},
                "relationships": {"workspace": {"data": {"type": "workspace", "id": "ws123"}}},
            }
        },
    )

    assert result.data.attributes.template_type == "default"
    assert result.data.attributes.is_template is True


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


@pytest.mark.asyncio
async def test_update_runbook_with_custom_field_values(mock_client_manager):
    """Test updating a runbook with custom field values."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": {
            "id": "rb123",
            "type": "runbook",
            "attributes": {
                "name": "Runbook with Custom Fields",
            },
        }
    }

    custom_fields = [
        {"name": "Environment", "value": "Production"},
        {"custom_field_id": "cf789", "value": ["Region A", "Region B"]},
    ]

    # Call the function
    await runbooks.update_runbook.fn(runbook_id="rb123", custom_field_values=custom_fields)

    # Verify custom_field_values is included in the payload
    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/runbooks/rb123",
        json_data={
            "data": {
                "type": "runbook",
                "id": "rb123",
                "attributes": {"custom_field_values": custom_fields},
            }
        },
    )


@pytest.mark.asyncio
async def test_get_runbook_template_copies(mock_client_manager):
    """Test fetching runbooks created from a template."""
    mock_client_manager.request.return_value = {
        "data": [
            {"id": "rb-copy-1", "type": "runbook", "attributes": {"name": "Copy 1"}},
            {"id": "rb-copy-2", "type": "runbook", "attributes": {"name": "Copy 2"}},
        ],
        "links": {},
    }

    result = await runbooks.get_runbook_template_copies.fn(runbook_id="rb-template")

    mock_client_manager.request.assert_called_once_with("GET", "core/runbooks?source_runbook_id=rb-template")

    assert len(result.data) == 2
    assert result.data[0].id == "rb-copy-1"
    assert result.data[1].attributes.name == "Copy 2"
    assert result.meta.page.total == 2
    assert result.links.self == "core/runbooks?source_runbook_id=rb-template"


@pytest.mark.asyncio
async def test_get_runbook_template_copies_with_pagination(mock_client_manager):
    """Test that template copies fetches all pages and meta.total reflects all collected items."""
    mock_client_manager.request.side_effect = [
        {
            "data": [{"id": "rb-copy-1", "type": "runbook", "attributes": {"name": "Copy 1"}}],
            "links": {"next": "core/runbooks?source_runbook_id=rb-template&cursor=abc123"},
        },
        {
            "data": [{"id": "rb-copy-2", "type": "runbook", "attributes": {"name": "Copy 2"}}],
            "links": {},
        },
    ]

    result = await runbooks.get_runbook_template_copies.fn(runbook_id="rb-template")

    assert mock_client_manager.request.call_count == 2
    calls = mock_client_manager.request.call_args_list
    assert calls[0][0] == ("GET", "core/runbooks?source_runbook_id=rb-template")
    assert calls[1][0] == ("GET", "core/runbooks?source_runbook_id=rb-template&cursor=abc123")

    assert len(result.data) == 2
    assert result.data[0].id == "rb-copy-1"
    assert result.data[1].id == "rb-copy-2"
    assert result.meta.page.total == 2
    assert result.links.self == "core/runbooks?source_runbook_id=rb-template"


@pytest.mark.asyncio
async def test_get_runbook_template_copies_empty(mock_client_manager):
    """Test fetching template copies when none exist."""
    mock_client_manager.request.return_value = {
        "data": [],
        "links": {},
    }

    result = await runbooks.get_runbook_template_copies.fn(runbook_id="rb-no-copies")

    assert len(result.data) == 0
    assert result.meta.page.total == 0
    assert result.links.self == "core/runbooks?source_runbook_id=rb-no-copies"
