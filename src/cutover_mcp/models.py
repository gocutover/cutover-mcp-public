from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

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


# --- 5. Runbook Models ---


class RunbookAttributes(BaseModel):
    name: str
    description: str | None = None
    archived: bool = False
    is_template: bool = Field(False, alias="is_template")
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


def inject_return_schema(func):
    """
    Dynamically injects the JSON schema of a function's Pydantic
    return type into its docstring.

    It replaces the placeholder '{return_schema}' with the schema.
    """
    if not func.__doc__:
        return func

    placeholder = "{return_schema}"
    if placeholder not in func.__doc__:
        return func

    # Get the return type annotation from the function signature
    try:
        return_model = func.__annotations__["return"]
    except KeyError:
        # No return annotation, so we can't do anything
        return func

    # Check if the annotation is a Pydantic model class
    if inspect.isclass(return_model) and issubclass(return_model, BaseModel):
        # Generate the schema from the discovered model and replace the placeholder
        schema_string = return_model.schema_json(indent=4)
        func.__doc__ = func.__doc__.replace(placeholder, schema_string)

    return func
