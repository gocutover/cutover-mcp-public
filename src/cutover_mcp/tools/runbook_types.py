from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr
from cutover_mcp.models import (
    RunbookTypeListResponse,
    RunbookTypeResponse,
    inject_return_schema,
)


async def _fetch_all_runbook_types() -> RunbookTypeListResponse:
    """Fetch every runbook type, following pagination links until exhausted.

    The pages are flattened into one synthetic response, so ``meta`` and ``links``
    describe the whole collection rather than whichever page happened to be last.
    """
    client = await client_mgr.get_client()
    all_data: list[dict] = []
    all_included: list[dict] = []
    seen_included: set[tuple[str | None, str | None]] = set()
    seen_paths: set[str] = set()
    path: str | None = "core/runbook_types"

    while path and path not in seen_paths:
        seen_paths.add(path)
        response = await client.request("GET", path)
        all_data.extend(response.get("data", []))
        for item in response.get("included") or []:
            key = (item.get("type"), item.get("id"))
            if key not in seen_included:
                seen_included.add(key)
                all_included.append(item)
        path = (response.get("links") or {}).get("next")

    return RunbookTypeListResponse(
        data=all_data,
        included=all_included,
        meta={"page": {"number": 1, "total": len(all_data)}},
        links={"self": "core/runbook_types"},
    )


@mcp.tool()
@inject_return_schema
async def list_runbook_types() -> RunbookTypeListResponse:
    """
    List all runbook types in the instance.

    :return: A RunbookTypeListResponse object containing a list of runbook types.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```
    """
    return await _fetch_all_runbook_types()


@mcp.tool()
@inject_return_schema
async def get_runbook_type_by_id(runbook_type_id: str) -> RunbookTypeResponse:
    """
    Fetch details for a specific runbook type by its ID.

    :param runbook_type_id: The unique identifier for the runbook type.
    :return: A RunbookTypeResponse object representing the runbook type.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```
    """
    client = await client_mgr.get_client()
    response = await client.request("GET", f"core/runbook_types/{runbook_type_id}")
    return RunbookTypeResponse(**response)


@mcp.tool()
@inject_return_schema
async def query_runbook_types(
    query: str | None = None,
    incident: bool | None = None,
    enable_rto: bool | None = None,
    dynamic: bool | None = None,
    ai_create_enabled: bool | None = None,
    include_archived: bool = False,
    include_disabled: bool = False,
) -> RunbookTypeListResponse:
    """
    Find runbook types matching a name/description search and/or capability flags.

    Use this to resolve a runbook type a user described in words into the ``id`` that
    ``create_runbook`` needs — e.g. "an incident runbook" (``incident=True``) or "a template
    with RTO/RTA enabled" (``enable_rto=True``). Every criterion is optional; passing none
    returns all usable runbook types. Multiple criteria are combined with AND.

    Filtering is applied client-side over the full collection because the public API
    ignores query parameters on ``core/runbook_types``.

    :param query: Case-insensitive substring matched against the name, key and description.
    :param incident: When set, keep only types whose ``incident`` flag matches.
    :param enable_rto: When set, keep only types whose ``enable_rto`` flag matches — these are
        the types supporting an RTO/RTA target.
    :param dynamic: When set, keep only types whose ``dynamic`` flag matches.
    :param ai_create_enabled: When set, keep only types whose ``ai_create_enabled`` flag matches.
    :param include_archived: Archived types are excluded by default because they cannot be used
        for new runbooks. Set True to include them.
    :param include_disabled: Disabled types are excluded by default because they cannot be used
        for new runbooks. Set True to include them.
    :return: A RunbookTypeListResponse containing only the matching runbook types, with
        ``meta.page.total`` reflecting the number of matches.

    JSON Schema of Return Object:
    ```json
    {return_schema}
    ```
    """
    listing = await _fetch_all_runbook_types()
    matches = listing.data

    if not include_archived:
        matches = [rt for rt in matches if not rt.attributes.archived]

    if not include_disabled:
        matches = [rt for rt in matches if not rt.attributes.disabled]

    for flag, wanted in (
        ("incident", incident),
        ("enable_rto", enable_rto),
        ("dynamic", dynamic),
        ("ai_create_enabled", ai_create_enabled),
    ):
        if wanted is not None:
            matches = [rt for rt in matches if getattr(rt.attributes, flag) is wanted]

    if query:
        needle = query.strip().casefold()
        matches = [
            rt
            for rt in matches
            if any(
                needle in field.casefold()
                for field in (rt.attributes.name, rt.attributes.key, rt.attributes.description)
                if field
            )
        ]

    return RunbookTypeListResponse(
        data=matches,
        included=listing.included,
        meta={"page": {"number": 1, "total": len(matches)}},
        links=listing.links,
    )
