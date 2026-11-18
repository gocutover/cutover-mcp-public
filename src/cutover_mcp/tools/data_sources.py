from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr


@mcp.tool()
async def get_data_source_upload_url(file_name: str, data_source_id: int | None = None) -> dict[str, Any]:
    """
    Get a short-lived, pre-signed URL for uploading a file that a data source reads from, such
    as a CMDB export in JSON or CSV.

    This server cannot read files on your machine, so upload the file yourself, straight away:
    send an HTTP PUT with the raw file as the body to the returned url before it expires
    (expires_in seconds). For example:

        curl --fail -X PUT --upload-file ./cmdb.csv "<url>"

    Keep the url in double quotes, because it contains & characters the shell would otherwise
    split on. Keep --fail, so a rejected upload exits with an error instead of looking like a
    success. If the upload fails or the url has expired, call this tool again for a new url
    rather than reusing the old one.

    For a new data source, create it with datasource_endpoint_url as its url. The file is
    scanned for malware after upload, so test the data source can read it before importing.

    :param file_name: Name of the file to upload, e.g. "cmdb.csv". Used to build the storage key.
    :param data_source_id: Omit for the first upload, before the data source exists. To upload a
        new version of the file behind an existing data source, pass that data source's ID. The
        new file only replaces the old one if the returned datasource_endpoint_url is the data
        source's current url; if it differs, the data source will not read this upload until its
        url is changed to the returned one. After uploading, refresh and sync the data source to
        pick up the changes.
    :return: url (PUT the file here), expires_in (seconds the url stays valid),
        datasource_endpoint_url (the url the data source reads the file from) and reference_id
        (the server-generated reference for the uploaded file).
    """
    if not file_name.strip():
        raise ValueError('file_name must be the name of the file to upload, e.g. "cmdb.csv".')

    client = await client_mgr.get_client()

    params = {"file_name": file_name}
    if data_source_id is not None:
        params["data_source_id"] = data_source_id

    response = await client.request("GET", "core/data_sources/upload_url", params=params)
    data = response.get("data", {})
    attributes = data.get("attributes", {})

    # Without an endpoint URL a data source has no way to read the uploaded file, so fail
    # before the caller uploads anything.
    if not attributes.get("datasource_endpoint_url"):
        raise ValueError(
            "The instance returned no datasource_endpoint_url, so its data source search service "
            "is not configured. A data source cannot read an uploaded file without it. Ask a "
            "Cutover administrator to configure the service for this instance."
        )

    return {
        "url": attributes.get("url"),
        "expires_in": attributes.get("expires_in"),
        "datasource_endpoint_url": attributes["datasource_endpoint_url"],
        "reference_id": data.get("id"),
    }
