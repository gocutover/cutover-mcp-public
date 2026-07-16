import pytest

from cutover_mcp.tools import runbook_types


@pytest.mark.asyncio
async def test_list_runbook_types(mock_client_manager):
    """Test listing all runbook types."""
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "1",
                "type": "runbook_type",
                "attributes": {
                    "name": "Normal runbook",
                    "key": "normal-runbook",
                    "description": "Standard runbook",
                    "archived": False,
                    "default": True,
                    "disabled": False,
                    "dynamic": False,
                    "enable_rto": True,
                    "global": True,
                    "incident": False,
                    "restrict_create_to_templates": False,
                    "ai_create_enabled": True,
                },
                "relationships": {},
            },
            {
                "id": "2",
                "type": "runbook_type",
                "attributes": {
                    "name": "Incident",
                    "key": "incident",
                    "description": "Incident runbook",
                    "archived": False,
                    "default": False,
                    "disabled": False,
                    "dynamic": True,
                    "enable_rto": False,
                    "global": True,
                    "incident": True,
                    "restrict_create_to_templates": True,
                    "ai_create_enabled": False,
                },
                "relationships": {},
            },
        ],
        "meta": {"page": {"number": 1, "total": 2}},
        "links": {"self": "core/runbook_types", "first": "core/runbook_types", "last": None, "prev": None, "next": None},
    }

    result = await runbook_types.list_runbook_types()

    mock_client_manager.request.assert_called_once_with("GET", "core/runbook_types")
    assert len(result.data) == 2
    assert result.data[0].attributes.name == "Normal runbook"
    assert result.data[0].attributes.key == "normal-runbook"
    assert result.data[0].attributes.enable_rto is True
    assert result.data[1].attributes.name == "Incident"
    assert result.data[1].attributes.incident is True


@pytest.mark.asyncio
async def test_list_runbook_types_pagination(mock_client_manager):
    """Test that list_runbook_types follows the next link to fetch all pages."""
    mock_client_manager.request.side_effect = [
        {
            "data": [
                {
                    "id": "1",
                    "type": "runbook_type",
                    "attributes": {"name": "Type 1", "key": "type-1"},
                    "relationships": {},
                }
            ],
            "meta": {"page": {"number": 1, "total": 2}},
            "links": {"next": "core/runbook_types?cursor=abc"},
        },
        {
            "data": [
                {
                    "id": "2",
                    "type": "runbook_type",
                    "attributes": {"name": "Type 2", "key": "type-2"},
                    "relationships": {},
                }
            ],
            "meta": {"page": {"number": 2, "total": 2}},
            "links": {"next": None},
        },
    ]

    result = await runbook_types.list_runbook_types()

    assert mock_client_manager.request.call_count == 2
    calls = mock_client_manager.request.call_args_list
    assert calls[0] == (("GET", "core/runbook_types"), {})
    assert calls[1] == (("GET", "core/runbook_types?cursor=abc"), {})
    assert len(result.data) == 2
    assert result.data[0].attributes.name == "Type 1"
    assert result.data[1].attributes.name == "Type 2"
