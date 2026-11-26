from mcp.types import ToolAnnotations

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)


def writes(*, destructive: bool, idempotent: bool, open_world: bool = False) -> ToolAnnotations:
    """
    Annotations for a tool that changes data in Cutover.

    :param destructive: True when the change cannot be undone: deleting or archiving, replacing a
        data source's file or records, or moving a runbook or task to another state. Creating and
        updating are not destructive, since an update can be set back.
    :param idempotent: True when calling it again with the same arguments changes nothing more.
    :param open_world: True when the tool reaches beyond the Cutover instance: it runs
        integrations, sends communications or fetches a URL the user configured.
    """
    return ToolAnnotations(
        read_only_hint=False, destructive_hint=destructive, idempotent_hint=idempotent, open_world_hint=open_world
    )
