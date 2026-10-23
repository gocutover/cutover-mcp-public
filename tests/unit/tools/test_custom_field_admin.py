from unittest.mock import call

import pytest

from cutover_mcp.tools import custom_fields


def _field_response(constraints=(), **attributes):
    return {
        "data": {
            "id": "501",
            "type": "custom_field",
            "attributes": {
                "name": "Layer",
                "field_type": "select_menu",
                "apply_to": "runbook_edit",
                "global": False,
                "archived": False,
                **attributes,
            },
            "relationships": {
                "workspace": {"data": {"id": "251", "type": "workspace"}},
                "custom_field_group": {"data": {"id": "7", "type": "custom_field_group"}},
                "constraints": {"data": [{"id": i, "type": t} for t, i in constraints]},
            },
        }
    }


# A field limited to task types 1 and 7 and runbook type 1.
CONSTRAINED = (("task_type", "1"), ("task_type", "7"), ("runbook_type", "1"))


@pytest.mark.asyncio
async def test_create_custom_field_workspace_select_menu(mock_client_manager):
    response = _field_response(field_options=[{"id": "1", "name": "App bug"}, {"id": "2", "name": "Infra"}])
    mock_client_manager.request.side_effect = [{"data": {"id": "501"}}, response]

    result = await custom_fields.create_custom_field(
        name="Layer",
        field_type="select_menu",
        apply_to="runbook_edit",
        workspace_id="251",
        field_options=["App bug", "Infra"],
        required=False,
        custom_field_group_id="7",
    )

    post, get = mock_client_manager.request.call_args_list
    assert get.args == ("GET", "core/custom_fields/501")
    assert post == call(
        "POST",
        "core/custom_fields",
        json_data={
            "data": {
                "type": "custom_field",
                "attributes": {
                    "name": "Layer",
                    "field_type": "select_menu",
                    "apply_to": "runbook_edit",
                    "global": False,
                    "field_options": [{"name": "App bug"}, {"name": "Infra"}],
                    "required": False,
                },
                "relationships": {
                    "workspace": {"data": {"id": "251", "type": "workspace"}},
                    "custom_field_group": {"data": {"id": "7", "type": "custom_field_group"}},
                },
            }
        },
    )
    assert result["id"] == "501"
    assert result["global"] is False
    assert result["workspace_id"] == "251"
    assert result["custom_field_group_id"] == "7"


@pytest.mark.asyncio
async def test_create_custom_field_global_text_has_no_relationships(mock_client_manager):
    mock_client_manager.request.return_value = {"data": {"id": "502", "attributes": {"global": True}}}

    result = await custom_fields.create_custom_field(
        name="Rootly INC", field_type="text", apply_to="runbook_edit", global_field=True
    )

    payload = mock_client_manager.request.call_args_list[0].kwargs["json_data"]
    assert payload == {
        "data": {
            "type": "custom_field",
            "attributes": {"name": "Rootly INC", "field_type": "text", "apply_to": "runbook_edit", "global": True},
        }
    }
    assert result["global"] is True
    assert result["workspace_id"] is None


@pytest.mark.asyncio
async def test_create_custom_field_merges_workspace_from_post(mock_client_manager):
    # POST returns workspace but not the group; GET returns the group but not workspace.
    post = {"data": {"id": "503", "relationships": {"workspace": {"data": {"id": "251", "type": "workspace"}}}}}
    get = {
        "data": {
            "id": "503",
            "attributes": {"name": "Layer"},
            "relationships": {"custom_field_group": {"data": {"id": "7", "type": "custom_field_group"}}},
        }
    }
    mock_client_manager.request.side_effect = [post, get]

    result = await custom_fields.create_custom_field(
        name="Layer", field_type="text", apply_to="runbook_edit", workspace_id="251", custom_field_group_id="7"
    )

    assert result["workspace_id"] == "251"
    assert result["custom_field_group_id"] == "7"


@pytest.mark.asyncio
async def test_create_custom_field_constraints(mock_client_manager):
    response = _field_response()
    response["data"]["relationships"]["constraints"] = {
        "data": [
            {"id": "1", "type": "task_type"},
            {"id": "464", "type": "task_type"},
            {"id": "1", "type": "runbook_type"},
        ]
    }
    mock_client_manager.request.return_value = response

    result = await custom_fields.create_custom_field(
        name="Seen before",
        field_type="text",
        apply_to="task_edit",
        workspace_id="251",
        task_type_ids=["1", "464"],
        runbook_type_ids=["1"],
    )

    relationships = mock_client_manager.request.call_args_list[0].kwargs["json_data"]["data"]["relationships"]
    assert result["task_type_ids"] == ["1", "464"]
    assert result["runbook_type_ids"] == ["1"]
    assert relationships["constraints"] == {
        "data": [
            {"id": "1", "type": "task_type"},
            {"id": "464", "type": "task_type"},
            {"id": "1", "type": "runbook_type"},
        ]
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({}, "exactly one of workspace_id or global_field"),
        ({"workspace_id": "251", "global_field": True}, "exactly one of workspace_id or global_field"),
        ({"workspace_id": "251", "field_type": "radiobox"}, "field_options is required"),
        ({"workspace_id": "251", "field_options": ["a"]}, "only allowed for select_menu"),
    ],
)
async def test_create_custom_field_rejects_bad_input_before_calling_api(mock_client_manager, kwargs, message):
    args = {"name": "X", "field_type": "text", "apply_to": "runbook_edit", **kwargs}

    with pytest.raises(ValueError, match=message):
        await custom_fields.create_custom_field(**args)

    mock_client_manager.request.assert_not_called()


@pytest.mark.asyncio
async def test_update_custom_field_sends_only_given_fields_and_keeps_group(mock_client_manager):
    current = _field_response()
    updated = _field_response(name="Layer v2")
    mock_client_manager.request.side_effect = [current, {"data": {"id": "501"}}, updated]

    result = await custom_fields.update_custom_field(
        "501", name="Layer v2", add_field_options=["Customer side"], display_search=True
    )

    get_current, patch, get_after = mock_client_manager.request.call_args_list
    assert get_current.args == ("GET", "core/custom_fields/501")
    assert get_after.args == ("GET", "core/custom_fields/501")
    # The current group is sent again: a PATCH without it removes the field from its group.
    assert patch == call(
        "PATCH",
        "core/custom_fields/501",
        json_data={
            "data": {
                "type": "custom_field",
                "id": "501",
                "attributes": {
                    "field_options": [{"name": "Customer side"}],
                    "name": "Layer v2",
                    "display_search": True,
                },
                "relationships": {"custom_field_group": {"data": {"id": "7", "type": "custom_field_group"}}},
            }
        },
    )
    assert result["name"] == "Layer v2"
    assert result["custom_field_group_id"] == "7"


@pytest.mark.asyncio
async def test_update_custom_field_without_group_sends_no_group(mock_client_manager):
    ungrouped = {"data": {"id": "501", "attributes": {"name": "Layer"}, "relationships": {}}}
    mock_client_manager.request.side_effect = [ungrouped, {"data": {"id": "501"}}, ungrouped]

    await custom_fields.update_custom_field("501", required=True)

    patch_payload = mock_client_manager.request.call_args_list[1].kwargs["json_data"]
    assert "relationships" not in patch_payload["data"]


@pytest.mark.asyncio
async def test_update_custom_field_moves_group(mock_client_manager):
    mock_client_manager.request.return_value = _field_response()

    await custom_fields.update_custom_field("501", custom_field_group_id="9")

    _, patch, _ = mock_client_manager.request.call_args_list
    assert patch.args == ("PATCH", "core/custom_fields/501")
    assert patch.kwargs["json_data"]["data"]["relationships"] == {
        "custom_field_group": {"data": {"id": "9", "type": "custom_field_group"}}
    }


@pytest.mark.asyncio
async def test_update_custom_field_empty_group_removes_field_from_group(mock_client_manager):
    mock_client_manager.request.return_value = _field_response()

    await custom_fields.update_custom_field("501", custom_field_group_id="")

    _, patch, _ = mock_client_manager.request.call_args_list
    data = patch.kwargs["json_data"]["data"]
    assert data["relationships"] == {"custom_field_group": {"data": None}}
    # A PATCH with empty attributes is rejected with 400 (seen on orc-01), so the name is resent.
    assert data["attributes"] == {"name": "Layer"}


@pytest.mark.asyncio
async def test_update_custom_field_rejects_options_on_non_option_field(mock_client_manager):
    mock_client_manager.request.return_value = _field_response(field_type="text")

    with pytest.raises(ValueError, match="only allowed for select_menu"):
        await custom_fields.update_custom_field("501", add_field_options=["x"])

    mock_client_manager.request.assert_called_once_with("GET", "core/custom_fields/501")


@pytest.mark.asyncio
async def test_update_custom_field_rejects_empty_constraint_list(mock_client_manager):
    # The API answers an empty constraints list with 400 Bad Request (seen on orc-01).
    with pytest.raises(ValueError, match="cannot be cleared"):
        await custom_fields.update_custom_field("501", task_type_ids=[])

    mock_client_manager.request.assert_not_called()


@pytest.mark.asyncio
async def test_update_custom_field_task_types_keep_runbook_types(mock_client_manager):
    # The PATCH replaces the whole constraints relationship, so the runbook types are sent again.
    mock_client_manager.request.return_value = _field_response(constraints=CONSTRAINED)

    await custom_fields.update_custom_field("501", task_type_ids=["1", "7", "8"])

    relationships = mock_client_manager.request.call_args_list[1].kwargs["json_data"]["data"]["relationships"]
    assert relationships["constraints"] == {
        "data": [
            {"id": "1", "type": "task_type"},
            {"id": "7", "type": "task_type"},
            {"id": "8", "type": "task_type"},
            {"id": "1", "type": "runbook_type"},
        ]
    }


@pytest.mark.asyncio
async def test_update_custom_field_runbook_types_keep_task_types(mock_client_manager):
    mock_client_manager.request.return_value = _field_response(constraints=CONSTRAINED)

    await custom_fields.update_custom_field("501", runbook_type_ids=["3"])

    relationships = mock_client_manager.request.call_args_list[1].kwargs["json_data"]["data"]["relationships"]
    assert relationships["constraints"] == {
        "data": [
            {"id": "1", "type": "task_type"},
            {"id": "7", "type": "task_type"},
            {"id": "3", "type": "runbook_type"},
        ]
    }


@pytest.mark.asyncio
async def test_update_custom_field_partial_constraints_with_group_move(mock_client_manager):
    mock_client_manager.request.return_value = _field_response(constraints=CONSTRAINED)

    await custom_fields.update_custom_field("501", custom_field_group_id="9", runbook_type_ids=["3"])

    relationships = mock_client_manager.request.call_args_list[1].kwargs["json_data"]["data"]["relationships"]
    assert relationships == {
        "custom_field_group": {"data": {"id": "9", "type": "custom_field_group"}},
        "constraints": {
            "data": [
                {"id": "1", "type": "task_type"},
                {"id": "7", "type": "task_type"},
                {"id": "3", "type": "runbook_type"},
            ]
        },
    }


@pytest.mark.asyncio
async def test_get_custom_field_returns_group_and_constraints(mock_client_manager):
    mock_client_manager.request.return_value = _field_response(constraints=CONSTRAINED)

    result = await custom_fields.get_custom_field("501")

    assert result["custom_field_group_id"] == "7"
    assert result["task_type_ids"] == ["1", "7"]
    assert result["runbook_type_ids"] == ["1"]


@pytest.mark.asyncio
async def test_update_custom_field_requires_a_change(mock_client_manager):
    with pytest.raises(ValueError, match="at least one field"):
        await custom_fields.update_custom_field("501")

    mock_client_manager.request.assert_not_called()


@pytest.mark.asyncio
async def test_archive_custom_field(mock_client_manager):
    mock_client_manager.request.return_value = {}

    result = await custom_fields.archive_custom_field("501")

    mock_client_manager.request.assert_called_once_with("PATCH", "core/custom_fields/501/archive")
    assert result == {"id": "501", "archived": True}


@pytest.mark.asyncio
async def test_list_custom_field_groups_paginates(mock_client_manager):
    mock_client_manager.request.side_effect = [
        {
            "data": [{"id": "1", "attributes": {"name": "Default", "default": True}}],
            "links": {"next": "core/custom_field_groups?page=2"},
        },
        {
            "data": [
                {"id": "7", "attributes": {"name": "Incident triage"}},
            ],
            "links": {},
        },
    ]

    result = await custom_fields.list_custom_field_groups()

    assert [call.args[1] for call in mock_client_manager.request.call_args_list] == [
        "core/custom_field_groups",
        "core/custom_field_groups?page=2",
    ]
    assert [group["id"] for group in result] == ["1", "7"]
    assert result[0]["default"] is True


@pytest.mark.asyncio
async def test_create_custom_field_group(mock_client_manager):
    mock_client_manager.request.return_value = {"data": {"id": "7", "attributes": {"name": "Incident triage"}}}

    result = await custom_fields.create_custom_field_group("Incident triage")

    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/custom_field_groups",
        json_data={"data": {"type": "custom_field_group", "attributes": {"name": "Incident triage"}}},
    )
    assert result == {"id": "7", "name": "Incident triage", "default": False}


@pytest.mark.asyncio
async def test_update_custom_field_group(mock_client_manager):
    mock_client_manager.request.return_value = {"data": {"id": "7", "attributes": {"name": "Triage"}}}

    result = await custom_fields.update_custom_field_group("7", "Triage")

    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/custom_field_groups/7",
        json_data={"data": {"type": "custom_field_group", "id": "7", "attributes": {"name": "Triage"}}},
    )
    assert result["name"] == "Triage"


@pytest.mark.asyncio
async def test_archive_custom_field_group(mock_client_manager):
    mock_client_manager.request.return_value = {}

    result = await custom_fields.archive_custom_field_group("7")

    mock_client_manager.request.assert_called_once_with("PATCH", "core/custom_field_groups/7/archive")
    assert result == {"id": "7", "archived": True}
