import pytest

from cutover_mcp.clients.api import CutoverAPIError
from cutover_mcp.tools import runbook_types


def _runbook_type(id_, name, key, description=None, **flags):
    """Build a runbook_type resource, defaulting every flag to False."""
    attributes = {
        "name": name,
        "key": key,
        "description": description,
        "archived": False,
        "default": False,
        "disabled": False,
        "dynamic": False,
        "enable_rto": False,
        "global": True,
        "incident": False,
        "restrict_create_to_templates": False,
        "ai_create_enabled": False,
    }
    attributes.update(flags)
    return {"id": id_, "type": "runbook_type", "attributes": attributes, "relationships": {}}


@pytest.fixture
def runbook_type_listing():
    """A single-page listing covering each flag and both excluded-by-default states."""
    return {
        "data": [
            _runbook_type("1", "Normal runbook", "normal-runbook", "Standard", enable_rto=True, dynamic=True),
            _runbook_type("3", "Recovery Plan", "recovery-plan", "Repeatable failover plan", enable_rto=True),
            _runbook_type("4", "RTO and AI", "rto-and-ai", "RTO RTA and AI", enable_rto=True, ai_create_enabled=True),
            _runbook_type("6", "Incident", "incident", "Incident", incident=True, dynamic=True),
            _runbook_type("8", "Retired Type", "retired", "No longer used", archived=True, enable_rto=True),
            _runbook_type("9", "Switched Off", "switched-off", "Turned off", disabled=True, enable_rto=True),
        ],
        "meta": {"page": {"number": 1, "total": 6}},
        "links": {"self": "core/runbook_types", "next": None},
    }


def _ids(result):
    return [rt.id for rt in result.data]


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
        "links": {
            "self": "core/runbook_types",
            "first": "core/runbook_types",
            "last": None,
            "prev": None,
            "next": None,
        },
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
    assert result.links.self == "core/runbook_types"


@pytest.mark.asyncio
async def test_list_runbook_types_pagination_aggregates_every_page(mock_client_manager):
    """Absolute next links are followed, and included/meta/links describe the whole collection."""
    workspace_10 = {"id": "10", "type": "workspace", "attributes": {"name": "Workspace 10"}}
    workspace_11 = {"id": "11", "type": "workspace", "attributes": {"name": "Workspace 11"}}
    workspace_12 = {"id": "12", "type": "workspace", "attributes": {"name": "Workspace 12"}}
    next_page = "https://api.example.com/core/runbook_types?page%5Bnumber%5D=2"
    mock_client_manager.request.side_effect = [
        {
            "data": [_runbook_type("1", "Type 1", "type-1")],
            "included": [workspace_10, workspace_11],
            "meta": {"page": {"number": 1, "total": 2}},
            "links": {"self": "https://api.example.com/core/runbook_types", "next": next_page},
        },
        {
            "data": [_runbook_type("2", "Type 2", "type-2")],
            "included": [workspace_11, workspace_12],
            "meta": {"page": {"number": 2, "total": 2}},
            "links": {"self": next_page, "next": None},
        },
    ]

    result = await runbook_types.list_runbook_types()

    assert [call.args[1] for call in mock_client_manager.request.call_args_list] == ["core/runbook_types", next_page]
    assert _ids(result) == ["1", "2"]
    # included is accumulated across pages and de-duplicated, not taken from the last page alone
    assert [(item.type, item.id) for item in result.included] == [
        ("workspace", "10"),
        ("workspace", "11"),
        ("workspace", "12"),
    ]
    # the flattened result is one synthetic page, so it must not describe the last page fetched
    assert result.meta.page.number == 1
    assert result.meta.page.total == 2
    assert result.links.self == "core/runbook_types"
    assert result.links.next is None


@pytest.mark.asyncio
async def test_list_runbook_types_stops_when_next_link_repeats(mock_client_manager):
    """A next link pointing at an already-fetched page terminates instead of looping forever."""
    mock_client_manager.request.return_value = {
        "data": [_runbook_type("1", "Type 1", "type-1")],
        "meta": {"page": {"number": 1, "total": 1}},
        "links": {"self": "core/runbook_types", "next": "core/runbook_types"},
    }

    result = await runbook_types.list_runbook_types()

    assert mock_client_manager.request.call_count == 1
    assert _ids(result) == ["1"]


@pytest.mark.asyncio
async def test_get_runbook_type_by_id(mock_client_manager):
    """Test fetching a single runbook type by its ID."""
    mock_client_manager.request.return_value = {
        "data": _runbook_type("6", "Incident", "incident", "Incident", incident=True, dynamic=True)
    }

    result = await runbook_types.get_runbook_type_by_id("6")

    mock_client_manager.request.assert_called_once_with("GET", "core/runbook_types/6")
    assert result.data.id == "6"
    assert result.data.type == "runbook_type"
    assert result.data.attributes.name == "Incident"
    assert result.data.attributes.key == "incident"
    assert result.data.attributes.incident is True


@pytest.mark.asyncio
async def test_get_runbook_type_by_id_not_found(mock_client_manager):
    """An unknown ID surfaces the API's error rather than returning an empty result."""
    mock_client_manager.request.side_effect = CutoverAPIError(
        status_code=404,
        url="https://api.example.com/core/runbook_types/9999",
        messages=["This link is not valid."],
        raw_body="",
    )

    with pytest.raises(CutoverAPIError) as exc_info:
        await runbook_types.get_runbook_type_by_id("9999")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_query_runbook_types_no_criteria_returns_usable_types(mock_client_manager, runbook_type_listing):
    """With no criteria, every type except archived and disabled ones is returned."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types()

    assert _ids(result) == ["1", "3", "4", "6"]
    assert result.meta.page.total == 4


@pytest.mark.asyncio
async def test_query_runbook_types_matches_name_case_insensitively(mock_client_manager, runbook_type_listing):
    """A text query matches the name regardless of case."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(query="INCIDENT")

    assert _ids(result) == ["6"]


@pytest.mark.asyncio
async def test_query_runbook_types_matches_description(mock_client_manager, runbook_type_listing):
    """A text query also matches the description, not just the name."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(query="failover")

    assert _ids(result) == ["3"]


@pytest.mark.asyncio
async def test_query_runbook_types_matches_key(mock_client_manager, runbook_type_listing):
    """A text query also matches the key."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(query="normal-runbook")

    assert _ids(result) == ["1"]


@pytest.mark.asyncio
async def test_query_runbook_types_no_match_returns_empty(mock_client_manager, runbook_type_listing):
    """A non-matching query returns nothing, never the unfiltered collection."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(query="no-such-type")

    assert result.data == []
    assert result.meta.page.total == 0


@pytest.mark.asyncio
async def test_query_runbook_types_by_flag(mock_client_manager, runbook_type_listing):
    """Filtering by a capability flag keeps only types with that flag set."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(enable_rto=True)

    assert _ids(result) == ["1", "3", "4"]


@pytest.mark.asyncio
async def test_query_runbook_types_flag_false_excludes_matches(mock_client_manager, runbook_type_listing):
    """Passing a flag as False keeps only types where it is unset."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(enable_rto=False)

    assert _ids(result) == ["6"]


@pytest.mark.asyncio
async def test_query_runbook_types_combines_criteria_with_and(mock_client_manager, runbook_type_listing):
    """Text and flag criteria are ANDed together."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(query="rto", enable_rto=True)

    assert _ids(result) == ["4"]


@pytest.mark.asyncio
async def test_query_runbook_types_can_include_archived_and_disabled(mock_client_manager, runbook_type_listing):
    """Archived and disabled types are reachable when explicitly requested."""
    mock_client_manager.request.return_value = runbook_type_listing

    result = await runbook_types.query_runbook_types(enable_rto=True, include_archived=True, include_disabled=True)

    assert _ids(result) == ["1", "3", "4", "8", "9"]


@pytest.mark.asyncio
async def test_query_runbook_types_follows_pagination(mock_client_manager):
    """Filtering considers every page, not just the first."""
    mock_client_manager.request.side_effect = [
        {
            "data": [_runbook_type("1", "Normal runbook", "normal-runbook")],
            "meta": {"page": {"number": 1, "total": 2}},
            "links": {"next": "core/runbook_types?cursor=abc"},
        },
        {
            "data": [_runbook_type("6", "Incident", "incident", incident=True)],
            "meta": {"page": {"number": 2, "total": 2}},
            "links": {"next": None},
        },
    ]

    result = await runbook_types.query_runbook_types(incident=True)

    assert mock_client_manager.request.call_count == 2
    assert _ids(result) == ["6"]
    assert result.links.self == "core/runbook_types"
