import json
import re
from typing import Any

from cutover_mcp.app import mcp
from cutover_mcp.clients.api import client_mgr

# Core masks the values of settings declared ``sensitive: true`` before they leave the API. Custom
# integrations declare no settings and some built-in credentials are undeclared, so names and values
# are screened here as well. A value is screened as a whole and by the keys it embeds: JSON members,
# query-string and form parameters, header lines. Screening is fail-closed: a descriptive setting may
# be dropped, a credential is never forwarded.
_SENSITIVE_SETTING = re.compile(
    r"(token|secret|password|passwd|credential|auth|key|header|username|user_name|cookie"
    r"|cert|pem|signing|signature|client_id|(^|_)arn(_|$))"
)
_SENSITIVE_VALUE = re.compile(
    r"""(authorization["']?\s*[:=]|\bbearer\s+\S+|\bbasic\s+[a-z0-9+/_-]+={0,2})""", re.IGNORECASE
)
_EMBEDDED_KEY = re.compile(r"""["']?([A-Za-z0-9_.-]+)["']?\s*[:=]""")
_URL_USERINFO = re.compile(r"://[^/?#\s@]+@")
_MASKED_VALUE = re.compile(r"^\*+$")
_MAX_VALUE_CHARS = 500


@mcp.tool()
async def list_task_types(include_integration: bool = True) -> dict[str, Any]:
    """
    List all task types, including the ones backed by an integration action.

    Use this to find the ``task_type_id`` for a task type by name ("Normal", "Milestone", "Email", ...)
    and to find the right type when a task should *do* something: run a Jenkins build, raise a
    ServiceNow change, post to Slack, call a webhook, or hand the task to an AI agent (an "agentic",
    "AI", "Cutover AI" or chat task).

    A task type backed by an integration carries a ``meta.integration_action`` object: ``kind``
    (``<provider>/<action>``, e.g. ``jenkins/build_job``, ``service_now/change_request``, ``custom/payload``,
    ``agentic/chat_cutover``), a ``definition`` with the ``title`` and ``description`` of that kind of action
    as declared by the integration, ``hooks`` (when it fires, usually ``task/started``) and a ``description``
    entered by the admin (often missing); plus ``integration_action`` / ``integration`` relationships, and
    its ``name`` is the integration action's name. Work out what a type does from the kind, definition,
    description and name.
    ``custom/payload`` types are admin-built HTTP integrations whose purpose is only in their name; call
    ``get_integration_task_type_details`` to see how one is configured when it matters.

    Agentic types: prefer ``agentic/chat_cutover`` (the built-in Cutover AI agent) over ``agentic/chat``
    (a customer-hosted agent) unless the user names one. For an agentic task set the task's ``message`` to
    the initial prompt the agent should receive when the task starts.

    :param include_integration: Include task types backed by an integration action (default true).
    :return: A dictionary containing a list of task types.
    """
    client = await client_mgr.get_client()
    params = {"include_integrations": "true"} if include_integration else None
    return await client.request("GET", "core/task_types", params=params)


@mcp.tool()
async def get_integration_task_type_details(integration_action_id: str) -> dict[str, Any]:
    """
    Get how an integration-backed task type is configured, to explain or choose it.

    Call this only when ``list_task_types`` does not make a type's purpose clear, typically a
    ``custom/payload`` type or one of several similar types. Pass the id from the task type's
    ``integration_action`` relationship. The result includes the action's name, kind, title, descriptions,
    hooks and its descriptive settings (target URLs, request type, response mode, polling, custom field
    mappings); credentials are never included.

    Reading integration actions needs the global ``Read IntegrationAction`` capability, held by global
    admins, integrations admins, global stakeholders and workspace stakeholders. Access to the runbook
    does not grant it, so runbook admins and workspace managers get a 403. On a 403, go by the
    task type's name and kind instead and tell the user why.

    :param integration_action_id: The integration action id from ``list_task_types``.
    :return: A dictionary summarising the integration action's configuration.
    """
    client = await client_mgr.get_client()
    response = await client.request("GET", f"core/integration_actions/{integration_action_id}")
    item = response.get("data") or {}
    attributes = item.get("attributes") or {}
    definition = (item.get("meta") or {}).get("definition") or {}
    relationships = item.get("relationships") or {}
    task_type = (relationships.get("task_type") or {}).get("data") or {}
    integration = (relationships.get("integration") or {}).get("data") or {}
    return {
        "integration_action_id": item.get("id"),
        "task_type_id": task_type.get("id"),
        "integration_id": integration.get("id"),
        "name": attributes.get("name"),
        "kind": attributes.get("kind"),
        "title": definition.get("title"),
        "kind_description": definition.get("description"),
        "description": attributes.get("description"),
        "hooks": attributes.get("hooks") or [],
        "settings": _descriptive_settings(attributes.get("settings") or {}),
        "option_overrides": attributes.get("option_overrides") or {},
    }


def _is_sensitive_value(text: str) -> bool:
    if _MASKED_VALUE.match(text) or _SENSITIVE_VALUE.search(text) or _URL_USERINFO.search(text):
        return True
    return any(_SENSITIVE_SETTING.search(key.lower()) for key in _EMBEDDED_KEY.findall(text))


def _descriptive_settings(settings: dict[str, Any]) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for key, value in (settings or {}).items():
        if value in (None, "", [], {}) or _SENSITIVE_SETTING.search(str(key).lower()):
            continue
        text = value if isinstance(value, str) else json.dumps(value, default=str)
        if _is_sensitive_value(text):
            continue
        kept[key] = text if len(text) <= _MAX_VALUE_CHARS else f"{text[:_MAX_VALUE_CHARS]}..."
    return kept
