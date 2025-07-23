from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar, Union, _GenericAlias, get_args, get_origin

from pydantic import BaseModel, Field

# --- 1. Generic JSON:API and Helper Models ---

# Type variables for creating generic models
AttributesType = TypeVar("AttributesType")
RelationshipsType = TypeVar("RelationshipsType")
DataType = TypeVar("DataType")


class JsonApiIdentifier(BaseModel):
    """A JSON:API resource identifier object."""

    id: str
    type: str


class Relationship(BaseModel, Generic[DataType]):
    """A JSON:API relationship object."""

    data: DataType | None = None
    links: dict[str, str] | None = None


class JsonApiObject(BaseModel, Generic[AttributesType, RelationshipsType]):
    """A generic JSON:API resource object."""

    id: str
    type: str
    attributes: AttributesType
    relationships: RelationshipsType | None = None
    links: dict[str, str] | None = None
    meta: dict[str, Any] | None = None


class PaginationLinks(BaseModel):
    """Pagination links for a list response."""

    self: str | None = None
    first: str | None = None
    last: str | None = None
    prev: str | None = None
    next: str | None = None


class PageMeta(BaseModel):
    """Pagination metadata."""

    number: int
    total: int | None = None


class ResponseMeta(BaseModel):
    """Top-level metadata for a list response."""

    page: PageMeta


class JsonApiListResponse(BaseModel, Generic[DataType]):
    """A generic model for a JSON:API list response."""

    data: list[DataType]
    meta: ResponseMeta
    links: PaginationLinks
    included: list[JsonApiObject] | None = []


class JsonApiSingleResponse(BaseModel, Generic[DataType]):
    """A generic model for a JSON:API single resource response."""

    data: DataType
    included: list[JsonApiObject] | None = []


# --- 2. Specific Resource Identifier Models ---


class UserIdentifier(JsonApiIdentifier):
    type: Literal["user"]


class GenericResourceIdentifier(JsonApiIdentifier):
    type: Literal["author", "folder", "runbook", "runbook_team", "task", "team", "stream", "user", "workspace"]


class RunbookIdentifier(JsonApiIdentifier):
    type: Literal["runbook"]


class TaskIdentifier(JsonApiIdentifier):
    type: Literal["task"]


class StreamIdentifier(JsonApiIdentifier):
    type: Literal["stream"]


class RunbookTeamIdentifier(JsonApiIdentifier):
    type: Literal["runbook_team"]


class TaskTypeIdentifier(JsonApiIdentifier):
    type: Literal["task_type"]


class RunbookVersionIdentifier(JsonApiIdentifier):
    type: Literal["runbook_version"]


# --- 3. Action Log Models ---


class ActionLogAttributes(BaseModel):
    event: str | None = None
    description: str | None = None
    changes: dict[str, Any] | None = None
    created_at: datetime | None = None


class ActionLogRelationships(BaseModel):
    author: Relationship[UserIdentifier] | None = None
    resource: Relationship[GenericResourceIdentifier] | None = None
    context: Relationship[GenericResourceIdentifier] | None = None


class ActionLogResource(JsonApiObject[ActionLogAttributes, ActionLogRelationships]):
    type: Literal["action_log"]


# Final Action Log Response Models
ActionLogResponse = JsonApiSingleResponse[ActionLogResource]
ActionLogListResponse = JsonApiListResponse[ActionLogResource]


# --- 4. Task Models ---


class CustomFieldValue(BaseModel):
    name: str | None = None
    custom_field_id: str | None = Field(None, alias="custom_field_id")
    value: str | list[str] | None
    display_name: str | None = Field(None, alias="display_name")
    read_only: bool | None = Field(None, alias="read_only")


class TaskAttributes(BaseModel):
    name: str
    description: str | None = None
    duration: int | None = None
    stage: Literal["not_startable", "startable", "in_progress", "complete"] | None = None
    start_planned: datetime | None = None
    end_planned: datetime | None = None
    start_actual: datetime | None = None
    end_actual: datetime | None = None
    start_fixed: datetime | None = None
    end_fixed: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    custom_field_values: list[CustomFieldValue] | None = Field(None, alias="custom_field_values")
    comments_count: int | None = Field(None, alias="comments_count")


class TaskRelationships(BaseModel):
    stream: Relationship[StreamIdentifier] | None = None
    task_type: Relationship[TaskTypeIdentifier] | None = Field(None, alias="task_type")
    assignees: Relationship[list[UserIdentifier | RunbookTeamIdentifier]] | None = None
    predecessors: Relationship[list[TaskIdentifier]] | None = None
    successors: Relationship[list[TaskIdentifier]] | None = None
    runbook_version: Relationship[RunbookVersionIdentifier] | None = Field(None, alias="runbook_version")


class TaskResource(JsonApiObject[TaskAttributes, TaskRelationships]):
    type: Literal["task"]


# Final Task Response Models
TaskResponse = JsonApiSingleResponse[TaskResource]
TaskListResponse = JsonApiListResponse[TaskResource]


# --- 5. Stream Models ---


class StreamAttributes(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None
    is_primary: bool | None = Field(None, alias="is_primary")
    status: Literal["off", "red", "amber", "green"] | None = None
    status_message: str | None = Field(None, alias="status_message")
    status_updated_at: datetime | None = Field(None, alias="status_updated_at")
    start_planned: datetime | None = Field(None, alias="start_planned")
    end_planned: datetime | None = Field(None, alias="end_planned")
    start_latest_planned: datetime | None = Field(None, alias="start_latest_planned")
    end_latest_planned: datetime | None = Field(None, alias="end_latest_planned")
    start_display: datetime | None = Field(None, alias="start_display")
    end_display: datetime | None = Field(None, alias="end_display")
    created_at: datetime | None = Field(None, alias="created_at")
    updated_at: datetime | None = Field(None, alias="updated_at")
    tasks_count: int | None = Field(None, alias="tasks_count")


class StreamRelationships(BaseModel):
    parent: Relationship[StreamIdentifier] | None = None
    runbook_version: Relationship[RunbookVersionIdentifier] | None = Field(None, alias="runbook_version")
    status_author: Relationship[UserIdentifier] | None = Field(None, alias="status_author")


class StreamResource(JsonApiObject[StreamAttributes, StreamRelationships]):
    type: Literal["stream"]


# Final Stream Response Models
StreamResponse = JsonApiSingleResponse[StreamResource]
StreamListResponse = JsonApiListResponse[StreamResource]


# --- 6. Runbook Models ---


class RunbookAttributes(BaseModel):
    name: str
    description: str | None = None
    archived: bool = False
    is_template: bool | None = Field(False, alias="is_template")
    stage: Literal["planning", "active", "paused", "canceled", "complete"] | None = None
    status: Literal["off", "red", "amber", "green"] | None = None
    template_type: Literal["off", "default", "snippet"] | None = Field(None, alias="template_type")
    start_planned: datetime | None = None
    end_planned: datetime | None = None
    start_scheduled: datetime | None = None
    end_scheduled: datetime | None = None
    start_actual: datetime | None = None
    end_actual: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    custom_field_values: list[CustomFieldValue] | None = Field(None, alias="custom_field_values")


class RunbookRelationships(BaseModel):
    workspace: Relationship[JsonApiIdentifier] | None = None
    folder: Relationship[JsonApiIdentifier] | None = None
    runbook_type: Relationship[JsonApiIdentifier] | None = Field(None, alias="runbook_type")
    author: Relationship[UserIdentifier] | None = None
    current_version: Relationship[RunbookVersionIdentifier] | None = Field(None, alias="current_version")


class RunbookResource(JsonApiObject[RunbookAttributes, RunbookRelationships]):
    type: Literal["runbook"]


# Final Runbook Response Models
RunbookResponse = JsonApiSingleResponse[RunbookResource]
RunbookListResponse = JsonApiListResponse[RunbookResource]


def generate_compact_schema_text(model: type[BaseModel], indent: int = 0, visited: set | None = None) -> str:
    """
    Recursively generates a compact, human-readable text representation
    of a Pydantic model's schema.
    """
    if visited is None:
        visited = set()

    if model in visited:
        return f"{' ' * indent}{model.__name__} (circular reference)\n"

    visited.add(model)

    schema_text = ""
    for field_name, field_info in model.model_fields.items():
        # Get the type annotation
        field_type = field_info.annotation

        # Handle optional types (Union[T, None])
        is_optional = False
        if get_origin(field_type) is Union:
            args = get_args(field_type)
            if len(args) == 2 and type(None) in args:
                is_optional = True
                # Get the non-None type
                field_type = args[0] if args[1] is type(None) else args[1]

        # Handle list types
        is_list = False
        if get_origin(field_type) in (list, _GenericAlias) and get_args(field_type):
            is_list = True
            list_item_type = get_args(field_type)[0]
            type_name = f"list[{list_item_type.__name__}]"
        else:
            type_name = getattr(field_type, "__name__", str(field_type))

        # Build the line for the current field
        line = f"{' ' * indent}{field_name}: {type_name}"
        if is_optional:
            line += " (optional)"
        schema_text += line + "\n"

        # Recurse for nested Pydantic models
        nested_model = None
        if is_list:
            # Check if the items in the list are Pydantic models
            if inspect.isclass(list_item_type) and issubclass(list_item_type, BaseModel):
                nested_model = list_item_type
        elif inspect.isclass(field_type) and issubclass(field_type, BaseModel):
            nested_model = field_type

        if nested_model:
            # Add a header for the nested definition and recurse
            schema_text += f"{' ' * (indent + 2)}-> {nested_model.__name__} details:\n"
            schema_text += generate_compact_schema_text(nested_model, indent + 4, visited)

    return schema_text


def inject_return_schema(func):
    """
    Dynamically injects a compact, token-efficient text representation of a
    function's Pydantic return type into its docstring.

    It replaces the placeholder '{return_schema}' with the compact schema.
    """
    if not func.__doc__:
        return func

    placeholder = "{return_schema}"
    if placeholder not in func.__doc__:
        return func

    try:
        return_model = func.__annotations__["return"]
    except KeyError:
        return func

    # Check if the annotation is a Pydantic model class
    if inspect.isclass(return_model) and issubclass(return_model, BaseModel):
        # Generate the compact schema and replace the placeholder
        schema_string = generate_compact_schema_text(return_model)
        func.__doc__ = func.__doc__.replace(placeholder, schema_string)

    return func
