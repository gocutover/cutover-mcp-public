from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr

PersistMode = Literal["query_cache", "persist_all"]


class DataSourceMapping(BaseModel):
    """One field of each record a data source reads."""

    model_config = ConfigDict(extra="forbid")

    mapping: str = Field(
        description=(
            "The key of the value in each source record, e.g. app_id. It is also the key in an "
            "imported record's values, and a searchable custom field's value_key must equal it."
        )
    )
    type: str = Field(default="text", description="The value type, e.g. text.")
    primary: bool = Field(
        default=False,
        description="True for exactly one mapping, whose value becomes each record's key.",
    )


def _build_data_source(item: dict[str, Any]) -> dict[str, Any]:
    attributes = item.get("attributes", {})
    return {
        "id": item.get("id"),
        "name": attributes.get("name"),
        "url": attributes.get("url"),
        "http_method": attributes.get("http_method"),
        "records_path": attributes.get("records_path"),
        "search_parameter_name": attributes.get("search_parameter_name"),
        "attributes_path": attributes.get("attributes_path"),
        "persist_mode": attributes.get("persist_mode"),
        "mappings": attributes.get("mappings") or [],
        "archivable": attributes.get("archivable"),
        "last_sync_status": attributes.get("last_sync_status"),
        "last_sync_error": attributes.get("last_sync_error"),
        "last_sync_started_at": attributes.get("last_sync_started_at"),
        "last_synced_at": attributes.get("last_synced_at"),
        "created_at": attributes.get("created_at"),
        "updated_at": attributes.get("updated_at"),
    }


@mcp.tool()
async def list_data_sources(archived: bool = False, query: str | None = None) -> list[dict[str, Any]]:
    """
    List the instance's JSON data sources. Data sources created by an integration are not
    returned. Requires the Custom Fields Admin or Global Stakeholder role.

    :param archived: Return archived data sources instead of active ones.
    :param query: Only return data sources whose name contains this text (case insensitive).
    :return: List of data sources, each in the same shape as get_data_source.
    """
    client = await client_mgr.get_client()

    params: dict[str, Any] | None = {"archived": "true" if archived else "false"}
    if query:
        params["query"] = query

    path: str | None = "core/data_sources"
    data_sources: list[dict[str, Any]] = []
    while path:
        response = await client.request("GET", path, params=params)
        params = None
        data_sources.extend(_build_data_source(item) for item in response.get("data", []))
        path = response.get("links", {}).get("next")

    return data_sources


@mcp.tool()
async def get_data_source(data_source_id: int) -> dict[str, Any]:
    """
    Get a data source. Requires the Custom Fields Admin or Global Stakeholder role.

    :param data_source_id: The ID of the data source (from list_data_sources).
    :return: id, name, url, http_method, records_path, search_parameter_name, attributes_path,
        persist_mode, mappings (each {mapping, type, primary}), archivable (False while an
        active custom field uses the data source, or once it is archived), last_sync_status
        (queued, running, succeeded or failed; None before the first import), last_sync_error,
        last_sync_started_at, last_synced_at, created_at and updated_at.
    """
    client = await client_mgr.get_client()
    response = await client.request("GET", f"core/data_sources/{data_source_id}")
    return _build_data_source(response.get("data", {}))


@mcp.tool()
async def create_data_source(
    name: str,
    url: str,
    mappings: list[DataSourceMapping],
    persist_mode: PersistMode | None = None,
    http_method: Literal["get", "post"] | None = None,
    records_path: str | None = None,
    search_parameter_name: str | None = None,
    attributes_path: str | None = None,
) -> dict[str, Any]:
    """
    Create a JSON data source, whose records back searchable custom fields. Authentication
    settings cannot be set through the API; create a data source that needs them in Cutover.

    For a data source over an uploaded file, pass the datasource_endpoint_url returned by
    get_data_source_upload_url as url and leave out records_path and search_parameter_name;
    Cutover sets them for an uploaded file.

    Requires the Custom Fields Admin role. persist_mode="persist_all" also requires Global
    Admin. Check list_data_sources first so an existing data source is reused.

    :param name: The data source's name.
    :param url: The endpoint searched for records, or an uploaded file's datasource_endpoint_url.
    :param mappings: The fields of each record, as {mapping, type, primary}. Exactly one must
        be primary; its value becomes each record's key. Map every column a searchable custom
        field or its dependent fields will show. For an uploaded file, each mapping is a key of
        the file's records.
    :param persist_mode: persist_all imports every record into Cutover; query_cache only stores
        the records a search returns. When omitted, Cutover's default applies.
    :param http_method: The HTTP method used to search url: get or post.
    :param records_path: The path to the array of records in the search response, e.g. .results.
    :param search_parameter_name: The query string parameter the search term is sent in.
    :param attributes_path: The path, relative to each record, to the object holding the
        mapped keys.
    :return: The created data source, in the same shape as get_data_source.
    """
    if not mappings:
        raise ValueError("Pass at least one mapping, with exactly one marked primary.")
    primaries = [m.mapping for m in mappings if m.primary]
    if len(primaries) != 1:
        raise ValueError(f"Exactly one mapping must be primary; got {len(primaries)}.")
    names = [m.mapping for m in mappings]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"Each mapping must be unique; repeated: {', '.join(duplicates)}.")

    attributes: dict[str, Any] = {
        "name": name,
        "url": url,
        "mappings": [m.model_dump() for m in mappings],
    }
    optional = {
        "persist_mode": persist_mode,
        "http_method": http_method,
        "records_path": records_path,
        "search_parameter_name": search_parameter_name,
        "attributes_path": attributes_path,
    }
    attributes.update({key: value for key, value in optional.items() if value is not None})

    client = await client_mgr.get_client()
    payload = {"data": {"type": "data_source", "attributes": attributes}}
    response = await client.request("POST", "core/data_sources", json_data=payload)
    return _build_data_source(response.get("data", {}))


@mcp.tool()
async def update_data_source(
    data_source_id: int,
    name: str | None = None,
    persist_mode: PersistMode | None = None,
) -> dict[str, Any]:
    """
    Rename a data source or change its persist mode. No other setting can be changed after
    creation; create a new data source instead.

    Requires the Custom Fields Admin role. Changing persist_mode also requires Global Admin.

    :param data_source_id: The ID of the data source (from list_data_sources).
    :param name: The new name.
    :param persist_mode: persist_all imports every record into Cutover; query_cache only
        stores the records a search returns.
    :return: The updated data source, in the same shape as get_data_source.
    """
    attributes = {key: value for key, value in {"name": name, "persist_mode": persist_mode}.items() if value}
    if not attributes:
        raise ValueError("Pass name, persist_mode or both.")

    client = await client_mgr.get_client()
    payload = {"data": {"type": "data_source", "id": str(data_source_id), "attributes": attributes}}
    response = await client.request("PATCH", f"core/data_sources/{data_source_id}", json_data=payload)
    return _build_data_source(response.get("data", {}))


@mcp.tool()
async def archive_data_source(data_source_id: int) -> dict[str, Any]:
    """
    Archive a data source. It cannot be archived while an active custom field uses it; archive
    those fields first. Requires the Custom Fields Admin role.

    :param data_source_id: The ID of the data source (from list_data_sources).
    :return: {"id": data_source_id, "archived": True} on success.
    """
    client = await client_mgr.get_client()
    await client.request("PATCH", f"core/data_sources/{data_source_id}/archive")
    return {"id": data_source_id, "archived": True}


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

    For a new data source, call create_data_source with datasource_endpoint_url as its url and
    leave out records_path and search_parameter_name. The file is scanned for malware after
    upload, so test the data source can read it before importing.

    :param file_name: Name of the file to upload, e.g. "cmdb.csv". Used to build the storage key.
    :param data_source_id: Omit for the first upload, before the data source exists. To upload a
        new version of the file behind a data source created over an uploaded file, pass that data
        source's ID; the new file replaces the old one. Fails, before any upload, if the data
        source reads from anywhere else, since its url cannot be changed: upload without
        data_source_id and create a new data source instead. After uploading, refresh and sync
        the data source to pick up the changes.
    :return: url (PUT the file here), expires_in (seconds the url stays valid),
        datasource_endpoint_url (the url the data source reads the file from) and reference_id
        (the server-generated reference for the uploaded file).
    """
    if not file_name.strip():
        raise ValueError('file_name must be the name of the file to upload, e.g. "cmdb.csv".')

    client = await client_mgr.get_client()

    params = {"file_name": file_name}
    current_url = None
    if data_source_id is not None:
        params["data_source_id"] = data_source_id
        current = await client.request("GET", f"core/data_sources/{data_source_id}")
        current_url = current.get("data", {}).get("attributes", {}).get("url")

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

    # Cutover reuses a data source's upload location only when the data source already reads from it.
    if data_source_id is not None and current_url != attributes["datasource_endpoint_url"]:
        raise ValueError(
            f"Data source {data_source_id} reads from {current_url}, not from this upload location, so "
            "it would never read the file, and its url cannot be changed. Call this tool without "
            "data_source_id, upload the file, and create a new data source with create_data_source."
        )

    return {
        "url": attributes.get("url"),
        "expires_in": attributes.get("expires_in"),
        "datasource_endpoint_url": attributes["datasource_endpoint_url"],
        "reference_id": data.get("id"),
    }
