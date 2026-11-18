import pytest

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
async def test_get_data_source_upload_url_new_version_passes_data_source_id(mock_client_manager):
    mock_client_manager.request.return_value = _upload_url_response()

    await data_sources.get_data_source_upload_url("cmdb.csv", data_source_id=42)

    mock_client_manager.request.assert_called_once_with(
        "GET", "core/data_sources/upload_url", params={"file_name": "cmdb.csv", "data_source_id": 42}
    )


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
