import re
from unittest.mock import AsyncMock, call, patch

import pytest
from pydantic import ValidationError

from cutover_mcp.clients.api import CutoverAPIError
from cutover_mcp.tools import data_sources


def _upload_url_response(**attributes):
    return {
        "data": {
            "id": "a1b2c3",
            "type": "data_source_upload_url",
            "attributes": {
                "url": "https://bucket.s3.amazonaws.com/a1b2c3/cmdb.csv?X-Amz-Signature=abc",
                "key": "a1b2c3/cmdb.csv",
                "expires_in": 900,
                "object_url": "https://bucket.s3.amazonaws.com/a1b2c3/cmdb.csv",
                "datasource_endpoint_url": "https://search.internal.cutover.cloud/a1b2c3",
                **attributes,
            },
        }
    }


@pytest.mark.asyncio
async def test_get_data_source_upload_url_first_upload(mock_client_manager):
    mock_client_manager.request.return_value = _upload_url_response()

    result = await data_sources.get_data_source_upload_url("cmdb.csv")

    mock_client_manager.request.assert_called_once_with(
        "GET", "core/data_sources/upload_url", params={"file_name": "cmdb.csv"}
    )
    assert result == {
        "url": "https://bucket.s3.amazonaws.com/a1b2c3/cmdb.csv?X-Amz-Signature=abc",
        "expires_in": 900,
        "datasource_endpoint_url": "https://search.internal.cutover.cloud/a1b2c3",
        "reference_id": "a1b2c3",
    }


@pytest.mark.asyncio
async def test_get_data_source_upload_url_new_version_for_a_data_source_over_the_same_location(mock_client_manager):
    endpoint = "https://search.internal.cutover.cloud/a1b2c3"
    mock_client_manager.request.side_effect = [
        {"data": {"id": "42", "attributes": {"url": endpoint}}},
        _upload_url_response(),
    ]

    result = await data_sources.get_data_source_upload_url("cmdb.csv", data_source_id=42)

    assert mock_client_manager.request.call_args_list == [
        call("GET", "core/data_sources/42"),
        call("GET", "core/data_sources/upload_url", params={"file_name": "cmdb.csv", "data_source_id": 42}),
    ]
    assert result["datasource_endpoint_url"] == endpoint


@pytest.mark.asyncio
async def test_get_data_source_upload_url_for_a_data_source_reading_elsewhere_raises(mock_client_manager):
    mock_client_manager.request.side_effect = [
        {"data": {"id": "42", "attributes": {"url": "https://cmdb.example.com/api/applications"}}},
        _upload_url_response(),
    ]

    with pytest.raises(
        ValueError, match=re.escape("reads from https://cmdb.example.com/api/applications, not from this upload")
    ):
        await data_sources.get_data_source_upload_url("cmdb.csv", data_source_id=42)


@pytest.mark.asyncio
async def test_get_data_source_upload_url_for_an_unknown_data_source_raises_the_api_error(mock_client_manager):
    mock_client_manager.request.side_effect = CutoverAPIError(404, "core/data_sources/999", ["Not found"])

    with pytest.raises(CutoverAPIError, match="Not found"):
        await data_sources.get_data_source_upload_url("cmdb.csv", data_source_id=999)

    mock_client_manager.request.assert_called_once_with("GET", "core/data_sources/999")


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint_url", ["", None])
async def test_get_data_source_upload_url_blank_endpoint_raises(mock_client_manager, endpoint_url):
    mock_client_manager.request.return_value = _upload_url_response(datasource_endpoint_url=endpoint_url)

    with pytest.raises(ValueError, match="search service is not configured"):
        await data_sources.get_data_source_upload_url("cmdb.csv")


@pytest.mark.asyncio
async def test_get_data_source_upload_url_missing_endpoint_raises(mock_client_manager):
    response = _upload_url_response()
    del response["data"]["attributes"]["datasource_endpoint_url"]
    mock_client_manager.request.return_value = response

    with pytest.raises(ValueError, match="search service is not configured"):
        await data_sources.get_data_source_upload_url("cmdb.csv")


@pytest.mark.asyncio
@pytest.mark.parametrize("file_name", ["", "   "])
async def test_get_data_source_upload_url_blank_file_name_raises_before_calling_the_api(mock_client_manager, file_name):
    with pytest.raises(ValueError, match="file_name must be the name of the file"):
        await data_sources.get_data_source_upload_url(file_name)

    mock_client_manager.request.assert_not_called()


def _data_source(id_="12", **attributes):
    return {
        "id": id_,
        "type": "data_source",
        "attributes": {
            "name": "Applications",
            "url": "https://search.internal.cutover.cloud/data_source/a1b2c3",
            "http_method": "get",
            "records_path": ".body.result",
            "search_parameter_name": "query",
            "attributes_path": None,
            "persist_mode": "persist_all",
            "mappings": [{"mapping": "app_id", "type": "text", "primary": True}],
            "archivable": True,
            "last_sync_status": None,
            "last_sync_error": None,
            "last_sync_started_at": None,
            "last_synced_at": None,
            "created_at": "2026-11-17T10:00:00Z",
            "updated_at": "2026-11-17T10:00:00Z",
            **attributes,
        },
    }


EXPECTED_DATA_SOURCE = {
    "id": "12",
    "name": "Applications",
    "url": "https://search.internal.cutover.cloud/data_source/a1b2c3",
    "http_method": "get",
    "records_path": ".body.result",
    "search_parameter_name": "query",
    "attributes_path": None,
    "persist_mode": "persist_all",
    "mappings": [{"mapping": "app_id", "type": "text", "primary": True}],
    "archivable": True,
    "last_sync_status": None,
    "last_sync_error": None,
    "last_sync_started_at": None,
    "last_synced_at": None,
    "created_at": "2026-11-17T10:00:00Z",
    "updated_at": "2026-11-17T10:00:00Z",
}

APP_ID = data_sources.DataSourceMapping(mapping="app_id", primary=True)
OWNER = data_sources.DataSourceMapping(mapping="owner")


@pytest.mark.asyncio
async def test_list_data_sources_follows_pages_and_sends_filters_once(mock_client_manager):
    mock_client_manager.request.side_effect = [
        {"data": [_data_source("12")], "links": {"next": "core/data_sources?page[number]=2&archived=true"}},
        {"data": [_data_source("13", name="Servers")], "links": {}},
    ]

    result = await data_sources.list_data_sources(archived=True, query="app")

    assert mock_client_manager.request.call_args_list == [
        call("GET", "core/data_sources", params={"archived": "true", "query": "app"}),
        call("GET", "core/data_sources?page[number]=2&archived=true", params=None),
    ]
    assert [(d["id"], d["name"]) for d in result] == [("12", "Applications"), ("13", "Servers")]


@pytest.mark.asyncio
async def test_list_data_sources_defaults_to_active(mock_client_manager):
    mock_client_manager.request.return_value = {"data": []}

    assert await data_sources.list_data_sources() == []

    mock_client_manager.request.assert_called_once_with("GET", "core/data_sources", params={"archived": "false"})


@pytest.mark.asyncio
async def test_get_data_source(mock_client_manager):
    mock_client_manager.request.return_value = {"data": _data_source()}

    result = await data_sources.get_data_source(12)

    mock_client_manager.request.assert_called_once_with("GET", "core/data_sources/12")
    assert result == EXPECTED_DATA_SOURCE


@pytest.mark.asyncio
async def test_create_data_source_over_uploaded_file_sends_only_given_attributes(mock_client_manager):
    mock_client_manager.request.return_value = {"data": _data_source()}

    result = await data_sources.create_data_source(
        name="Applications",
        url="https://search.internal.cutover.cloud/data_source/a1b2c3",
        mappings=[APP_ID, OWNER],
        persist_mode="persist_all",
    )

    mock_client_manager.request.assert_called_once_with(
        "POST",
        "core/data_sources",
        json_data={
            "data": {
                "type": "data_source",
                "attributes": {
                    "name": "Applications",
                    "url": "https://search.internal.cutover.cloud/data_source/a1b2c3",
                    "mappings": [
                        {"mapping": "app_id", "type": "text", "primary": True},
                        {"mapping": "owner", "type": "text", "primary": False},
                    ],
                    "persist_mode": "persist_all",
                },
            }
        },
    )
    assert result == EXPECTED_DATA_SOURCE


@pytest.mark.asyncio
async def test_create_data_source_over_endpoint_sends_search_settings(mock_client_manager):
    mock_client_manager.request.return_value = {"data": _data_source()}

    await data_sources.create_data_source(
        name="Applications",
        url="https://cmdb.example.com/api/applications",
        mappings=[APP_ID],
        persist_mode="query_cache",
        http_method="post",
        records_path=".results",
        search_parameter_name="q",
        attributes_path=".fields",
    )

    attributes = mock_client_manager.request.call_args.kwargs["json_data"]["data"]["attributes"]
    assert attributes == {
        "name": "Applications",
        "url": "https://cmdb.example.com/api/applications",
        "mappings": [{"mapping": "app_id", "type": "text", "primary": True}],
        "persist_mode": "query_cache",
        "http_method": "post",
        "records_path": ".results",
        "search_parameter_name": "q",
        "attributes_path": ".fields",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mappings", "message"),
    [
        ([], "at least one mapping"),
        ([OWNER], "Exactly one mapping must be primary; got 0"),
        ([APP_ID, data_sources.DataSourceMapping(mapping="name", primary=True)], "got 2"),
        ([APP_ID, OWNER, OWNER], "repeated: owner"),
    ],
)
async def test_create_data_source_rejects_invalid_mappings_before_calling_the_api(
    mock_client_manager, mappings, message
):
    with pytest.raises(ValueError, match=message):
        await data_sources.create_data_source(name="Applications", url="https://x", mappings=mappings)

    mock_client_manager.request.assert_not_called()


def test_data_source_mapping_rejects_label():
    with pytest.raises(ValidationError, match="label"):
        data_sources.DataSourceMapping(mapping="app_id", label="Application ID")


@pytest.mark.asyncio
async def test_update_data_source_sends_only_given_attributes(mock_client_manager):
    mock_client_manager.request.return_value = {"data": _data_source(name="Apps")}

    result = await data_sources.update_data_source(12, name="Apps")

    mock_client_manager.request.assert_called_once_with(
        "PATCH",
        "core/data_sources/12",
        json_data={"data": {"type": "data_source", "id": "12", "attributes": {"name": "Apps"}}},
    )
    assert result["name"] == "Apps"


@pytest.mark.asyncio
async def test_update_data_source_without_changes_raises_before_calling_the_api(mock_client_manager):
    with pytest.raises(ValueError, match="Pass name, persist_mode or both"):
        await data_sources.update_data_source(12)

    mock_client_manager.request.assert_not_called()


@pytest.mark.asyncio
async def test_archive_data_source(mock_client_manager):
    mock_client_manager.request.return_value = {}

    result = await data_sources.archive_data_source(12)

    mock_client_manager.request.assert_called_once_with("PATCH", "core/data_sources/12/archive")
    assert result == {"id": 12, "archived": True}


@pytest.mark.asyncio
async def test_manage_data_source_test_returns_the_endpoint_response_truncated(mock_client_manager):
    body = "x" * 2500
    mock_client_manager.request.return_value = {
        "data": {"attributes": {"status": 200, "url": "https://ds/abc?query=%2A", "body": body}}
    }

    result = await data_sources.manage_data_source(12, "test")

    mock_client_manager.request.assert_called_once_with("GET", "core/data_sources/12/test", params={"query": "*"})
    assert result == {
        "id": 12,
        "action": "test",
        "status": 200,
        "url": "https://ds/abc?query=%2A",
        "body": "x" * 2000,
        "body_truncated": True,
    }


@pytest.mark.asyncio
async def test_manage_data_source_refresh_returns_the_number_of_keys_added(mock_client_manager):
    mock_client_manager.request.return_value = {"data": {"attributes": {"total_added": 3}}}

    result = await data_sources.manage_data_source(12, "refresh", query="APP-0001")

    mock_client_manager.request.assert_called_once_with(
        "PATCH", "core/data_sources/12/refresh", params={"query": "APP-0001"}
    )
    assert result == {"id": 12, "action": "refresh", "total_added": 3}


def _sync_state(status, started_at=None, error=None):
    return {"data": _data_source(last_sync_status=status, last_sync_started_at=started_at, last_sync_error=error)}


@pytest.fixture
def fake_clock():
    clock = [0.0]

    async def sleep(seconds):
        clock[0] += seconds

    with (
        patch.object(data_sources, "_now", side_effect=lambda: clock[0]),
        patch.object(data_sources.asyncio, "sleep", new=AsyncMock(side_effect=sleep)) as sleep_mock,
    ):
        yield sleep_mock


@pytest.mark.asyncio
async def test_sync_waits_until_its_own_import_finishes(mock_client_manager, fake_clock):
    mock_client_manager.request.side_effect = [
        _sync_state("succeeded", "2026-11-17T05:00:00Z"),
        {},
        _sync_state("succeeded", "2026-11-17T05:00:00Z"),
        _sync_state("running", "2026-11-18T15:00:00Z"),
        _sync_state("succeeded", "2026-11-18T15:00:00Z"),
    ]

    result = await data_sources.manage_data_source(12, "sync")

    assert mock_client_manager.request.call_args_list[1] == call("POST", "core/data_sources/12/sync")
    assert fake_clock.await_count == 2
    assert result["finished"] is True
    assert result["already_running"] is False
    assert result["last_sync_status"] == "succeeded"
    assert result["last_sync_started_at"] == "2026-11-18T15:00:00Z"
    assert "message" not in result


@pytest.mark.asyncio
async def test_sync_reports_a_failed_import_with_its_error(mock_client_manager, fake_clock):
    mock_client_manager.request.side_effect = [
        _sync_state(None),
        {},
        _sync_state("failed", "2026-11-18T15:00:00Z", "1 of 4 records could not be saved"),
    ]

    result = await data_sources.manage_data_source(12, "sync")

    assert result["finished"] is True
    assert result["last_sync_status"] == "failed"
    assert result["last_sync_error"] == "1 of 4 records could not be saved"


@pytest.mark.asyncio
async def test_sync_joins_an_import_already_in_progress_when_the_api_answers_409(mock_client_manager, fake_clock):
    mock_client_manager.request.side_effect = [
        _sync_state("running", "2026-11-18T15:00:00Z"),
        CutoverAPIError(409, "core/data_sources/12/sync", ["An import is already in progress for this data source."]),
        _sync_state("succeeded", "2026-11-18T15:00:00Z"),
    ]

    result = await data_sources.manage_data_source(12, "sync")

    assert result["finished"] is True
    assert result["already_running"] is True
    assert result["last_sync_status"] == "succeeded"


@pytest.mark.asyncio
async def test_sync_returns_a_message_when_the_import_outlasts_wait_seconds(mock_client_manager, fake_clock):
    mock_client_manager.request.side_effect = [_sync_state("succeeded", "2026-11-17T05:00:00Z"), {}] + [
        _sync_state("queued", "2026-11-17T05:00:00Z")
    ] * 3

    result = await data_sources.manage_data_source(12, "sync", wait_seconds=10)

    assert fake_clock.await_count == 2
    assert result["finished"] is False
    assert result["last_sync_status"] == "queued"
    assert result["message"].startswith("The import had not finished after 10 seconds.")


@pytest.mark.asyncio
async def test_sync_with_no_wait_returns_once_queued(mock_client_manager, fake_clock):
    mock_client_manager.request.side_effect = [_sync_state(None), {}, _sync_state("queued")]

    result = await data_sources.manage_data_source(12, "sync", wait_seconds=0)

    fake_clock.assert_not_awaited()
    assert result["finished"] is False
    assert result["last_sync_status"] == "queued"


@pytest.mark.asyncio
async def test_sync_passes_on_other_api_errors(mock_client_manager, fake_clock):
    refused = CutoverAPIError(422, "core/data_sources/12/sync", ["Data source must persist all records."])
    mock_client_manager.request.side_effect = [_sync_state(None), refused]

    with pytest.raises(CutoverAPIError) as raised:
        await data_sources.manage_data_source(12, "sync")

    assert raised.value is refused


@pytest.mark.asyncio
@pytest.mark.parametrize("wait_seconds", [-1, 51])
async def test_sync_rejects_wait_seconds_out_of_range_before_calling_the_api(mock_client_manager, wait_seconds):
    with pytest.raises(ValueError, match="wait_seconds must be between 0 and 50"):
        await data_sources.manage_data_source(12, "sync", wait_seconds=wait_seconds)

    mock_client_manager.request.assert_not_called()


@pytest.mark.asyncio
async def test_sync_does_not_report_an_earlier_running_import_as_its_own(mock_client_manager, fake_clock):
    mock_client_manager.request.side_effect = [
        _sync_state("running", "2026-11-18T15:00:00Z"),
        {},
        _sync_state("succeeded", "2026-11-18T15:00:00Z"),
        _sync_state("running", "2026-11-18T15:01:00Z"),
        _sync_state("succeeded", "2026-11-18T15:01:00Z"),
    ]

    result = await data_sources.manage_data_source(12, "sync")

    assert result["finished"] is True
    assert result["already_running"] is False
    assert result["last_sync_started_at"] == "2026-11-18T15:01:00Z"


@pytest.mark.asyncio
async def test_wait_seconds_is_only_checked_for_sync(mock_client_manager):
    mock_client_manager.request.return_value = {"data": {"attributes": {"status": 200, "body": "[]"}}}

    result = await data_sources.manage_data_source(12, "test", wait_seconds=600)

    assert result["status"] == 200


@pytest.mark.asyncio
async def test_list_data_source_values_returns_one_page(mock_client_manager):
    mock_client_manager.request.return_value = {
        "data": [
            {"id": "1", "attributes": {"key": "APP-0001", "values": {"app_id": "APP-0001", "owner": "Payments"}}},
            {"id": "2", "attributes": {"key": "APP-0002", "values": {"app_id": "APP-0002"}}},
        ],
        "meta": {"page": {"number": 2, "total": 45}},
        "links": {"next": "https://api.example.com/core/custom_fields/756/data_source_values?page[number]=3"},
    }

    result = await data_sources.list_data_source_values("756", page=2)

    mock_client_manager.request.assert_called_once_with(
        "GET", "core/custom_fields/756/data_source_values", params={"page[number]": 2}
    )
    assert result == {
        "values": [
            {"key": "APP-0001", "values": {"app_id": "APP-0001", "owner": "Payments"}},
            {"key": "APP-0002", "values": {"app_id": "APP-0002"}},
        ],
        "page": 2,
        "total_records": 45,
        "has_more": True,
    }


@pytest.mark.asyncio
async def test_list_data_source_values_last_page_has_no_more(mock_client_manager):
    mock_client_manager.request.return_value = {"data": [], "meta": {"page": {"number": 3, "total": 45}}, "links": {}}

    result = await data_sources.list_data_source_values("756", page=3)

    assert result["has_more"] is False


@pytest.mark.asyncio
async def test_list_data_source_values_rejects_a_page_below_1_before_calling_the_api(mock_client_manager):
    with pytest.raises(ValueError, match="page must be 1 or more"):
        await data_sources.list_data_source_values("756", page=0)

    mock_client_manager.request.assert_not_called()


@pytest.mark.asyncio
async def test_list_data_source_values_returns_an_empty_dict_for_null_values(mock_client_manager):
    mock_client_manager.request.return_value = {"data": [{"attributes": {"key": "APP-0001", "values": None}}]}

    result = await data_sources.list_data_source_values("756")

    assert result["values"] == [{"key": "APP-0001", "values": {}}]
