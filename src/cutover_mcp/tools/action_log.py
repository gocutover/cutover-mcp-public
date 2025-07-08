from typing import Optional
from cutover_mcp.app import mcp  
from cutover_mcp.clients.api import client_mgr

@mcp.tool()
async def get_action_logs(
    runbook_id: Optional[str] = None, user_id: Optional[str] = None, workspace_id: Optional[str] = None,
    created_after: Optional[str] = None, created_before: Optional[str] = None,
    page_size: int = 50, page_number: int = 1
) -> dict:
    """
    Retrieve action logs (audit logs) from Cutover.

    :param limit: The maximum number of log entries to return. Defaults to 100.
    :param offset: The number of log entries to skip.
    :param filter_string: A string to filter the log entries by.
    :param start_time: The start of the time range for logs (ISO 8601 format).
    :param end_time: The end of the time range for logs (ISO 8601 format).
    :return: A dictionary containing a list of action log entries.
    """
    
    client = client_mgr.get_client()
    params = {"page[number]": page_number, "page[size]": page_size}
    if runbook_id: params["runbook_id"] = runbook_id
    if user_id: params["user_id"] = user_id
    if workspace_id: params["workspace_id"] = workspace_id
    if created_after: params["created_after"] = created_after
    if created_before: params["created_before"] = created_before
    return await client.request("GET", "core/action_logs", params=params)
