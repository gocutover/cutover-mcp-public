import pytest

from cutover_mcp.tools import folders


FOLDER_1 = {
    "id": "1",
    "type": "folder",
    "attributes": {
        "name": "Default",
        "description": "",
        "created_at": "2025-11-10T15:47:10Z",
        "updated_at": "2026-03-24T15:17:18Z",
    },
    "relationships": {
        "parent": None,
        "workspace": {
            "data": {"id": "1", "type": "workspace"},
            "links": {"related": "https://api.cutover.com/core/workspaces/1"},
        },
    },
    "links": {},
    "meta": {"permissions": [{"type": "create", "resource": "runbook"}]},
}

FOLDER_64 = {
    "id": "64",
    "type": "folder",
    "attributes": {
        "name": "another folder",
        "description": "",
        "created_at": "2026-04-02T16:47:15Z",
        "updated_at": "2026-04-02T16:47:15Z",
    },
    "relationships": {
        "parent": {
            "data": {"id": "63", "type": "folder"},
            "links": None,
        },
        "workspace": {
            "data": {"id": "1", "type": "workspace"},
            "links": {"related": "https://api.cutover.com/core/workspaces/1"},
        },
    },
    "links": {},
    "meta": {"permissions": [{"type": "create", "resource": "runbook"}]},
}


@pytest.mark.asyncio
async def test_list_folders(mock_client_manager):
    """Test listing folders in a workspace."""
    mock_client_manager.request.return_value = {
        "data": [FOLDER_1],
        "meta": {"page": {"number": 1, "total": None}},
        "links": {"self": "https://api.cutover.com/core/workspaces/1/folders", "next": None},
    }

    result = await folders.list_folders(workspace_id="1")

    mock_client_manager.request.assert_called_once_with("GET", "core/workspaces/1/folders")

    assert len(result.data) == 1
    assert result.data[0].id == "1"
    assert result.data[0].attributes.name == "Default"
    assert result.data[0].relationships.parent is None


@pytest.mark.asyncio
async def test_list_folders_with_subfolder(mock_client_manager):
    """Test that sub-folder parent relationships are correctly parsed."""
    mock_client_manager.request.return_value = {
        "data": [FOLDER_1, FOLDER_64],
        "meta": {"page": {"number": 1, "total": None}},
        "links": {"self": "https://api.cutover.com/core/workspaces/1/folders", "next": None},
    }

    result = await folders.list_folders(workspace_id="1")

    assert len(result.data) == 2

    top_level = result.data[0]
    assert top_level.relationships.parent is None

    subfolder = result.data[1]
    assert subfolder.relationships.parent.data.id == "63"
    assert subfolder.relationships.parent.data.type == "folder"


@pytest.mark.asyncio
async def test_list_folders_empty(mock_client_manager):
    """Test listing folders when workspace has no folders."""
    mock_client_manager.request.return_value = {
        "data": [],
        "meta": {"page": {"number": 1, "total": None}},
        "links": {"self": "https://api.cutover.com/core/workspaces/1/folders", "next": None},
    }

    result = await folders.list_folders(workspace_id="1")

    assert len(result.data) == 0


@pytest.mark.asyncio
async def test_list_folders_pagination(mock_client_manager):
    """Test that list_folders follows pagination and returns all folders."""
    mock_client_manager.request.side_effect = [
        {
            "data": [FOLDER_1],
            "meta": {"page": {"number": 1, "total": None}},
            "links": {
                "self": "https://api.cutover.com/core/workspaces/1/folders",
                "next": "https://api.cutover.com/core/workspaces/1/folders?page[number]=2",
            },
        },
        {
            "data": [FOLDER_64],
            "meta": {"page": {"number": 2, "total": None}},
            "links": {
                "self": "https://api.cutover.com/core/workspaces/1/folders?page[number]=2",
                "next": None,
            },
        },
    ]

    result = await folders.list_folders(workspace_id="1")

    assert mock_client_manager.request.call_count == 2

    # Verify that the first request uses the initial folders endpoint
    first_call = mock_client_manager.request.call_args_list[0]
    assert first_call.args[1] == "core/workspaces/1/folders"

    # Verify that the second request follows the `links.next` URL
    second_call = mock_client_manager.request.call_args_list[1]
    assert (
        second_call.args[1]
        == "https://api.cutover.com/core/workspaces/1/folders?page[number]=2"
    )
    assert len(result.data) == 2
    assert result.data[0].id == "1"
    assert result.data[1].id == "64"
