from __future__ import annotations
from datetime import datetime
from typing import Any, Generic, List, Literal, Optional, TypeVar, Union
import inspect
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
    data: Optional[DataType] = None
    links: Optional[dict[str, str]] = None

class JsonApiObject(BaseModel, Generic[AttributesType, RelationshipsType]):
    """A generic JSON:API resource object."""
    id: str
    type: str
    attributes: AttributesType
    relationships: Optional[RelationshipsType] = None
    links: Optional[dict[str, str]] = None
    meta: Optional[dict[str, Any]] = None

class PaginationLinks(BaseModel):
    """Pagination links for a list response."""
    self: Optional[str] = None
    first: Optional[str] = None
    last: Optional[str] = None
    prev: Optional[str] = None
    next: Optional[str] = None

class PageMeta(BaseModel):
    """Pagination metadata."""
    number: int
    total: Optional[int] = None

class ResponseMeta(BaseModel):
    """Top-level metadata for a list response."""
    page: PageMeta

class JsonApiListResponse(BaseModel, Generic[DataType]):
    """A generic model for a JSON:API list response."""
    data: List[DataType]
    meta: ResponseMeta
    links: PaginationLinks
    included: Optional[List[JsonApiObject]] = []

class JsonApiSingleResponse(BaseModel, Generic[DataType]):
    """A generic model for a JSON:API single resource response."""
    data: DataType
    included: Optional[List[JsonApiObject]] = []

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
    event: Optional[str] = None
    description: Optional[str] = None
    changes: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None

class ActionLogRelationships(BaseModel):
    author: Optional[Relationship[UserIdentifier]] = None
    resource: Optional[Relationship[GenericResourceIdentifier]] = None
    context: Optional[Relationship[GenericResourceIdentifier]] = None

class ActionLogResource(JsonApiObject[ActionLogAttributes, ActionLogRelationships]):
    type: Literal["action_log"]

# Final Action Log Response Models
ActionLogResponse = JsonApiSingleResponse[ActionLogResource]
ActionLogListResponse = JsonApiListResponse[ActionLogResource]


# --- 4. Task Models ---

class CustomFieldValue(BaseModel):
    name: Optional[str] = None
    custom_field_id: Optional[str] = Field(None, alias="custom_field_id")
    value: Union[str, List[str], None]
    display_name: Optional[str] = Field(None, alias="display_name")
    read_only: Optional[bool] = Field(None, alias="read_only")

class TaskAttributes(BaseModel):
    name: str
    description: Optional[str] = None
    duration: Optional[int] = None
    stage: Optional[Literal["not_startable", "startable", "in_progress", "complete"]] = None
    start_planned: Optional[datetime] = None
    end_planned: Optional[datetime] = None
    start_actual: Optional[datetime] = None
    end_actual: Optional[datetime] = None
    start_fixed: Optional[datetime] = None
    end_fixed: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    custom_field_values: Optional[List[CustomFieldValue]] = Field(None, alias="custom_field_values")
    comments_count: Optional[int] = Field(None, alias="comments_count")

class TaskRelationships(BaseModel):
    stream: Optional[Relationship[StreamIdentifier]] = None
    task_type: Optional[Relationship[TaskTypeIdentifier]] = Field(None, alias="task_type")
    assignees: Optional[Relationship[List[Union[UserIdentifier, RunbookTeamIdentifier]]]] = None
    predecessors: Optional[Relationship[List[TaskIdentifier]]] = None
    successors: Optional[Relationship[List[TaskIdentifier]]] = None
    runbook_version: Optional[Relationship[RunbookVersionIdentifier]] = Field(None, alias="runbook_version")

class TaskResource(JsonApiObject[TaskAttributes, TaskRelationships]):
    type: Literal["task"]

# Final Task Response Models
TaskResponse = JsonApiSingleResponse[TaskResource]
TaskListResponse = JsonApiListResponse[TaskResource]


# --- 5. Runbook Models ---

class RunbookAttributes(BaseModel):
    name: str
    description: Optional[str] = None
    archived: bool = False
    is_template: bool = Field(False, alias="is_template")
    stage: Optional[Literal["planning", "active", "paused", "canceled", "complete"]] = None
    status: Optional[Literal["off", "red", "amber", "green"]] = None
    template_type: Optional[Literal["off", "default", "snippet"]] = Field(None, alias="template_type")
    start_planned: Optional[datetime] = None
    end_planned: Optional[datetime] = None
    start_scheduled: Optional[datetime] = None
    end_scheduled: Optional[datetime] = None
    start_actual: Optional[datetime] = None
    end_actual: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    custom_field_values: Optional[List[CustomFieldValue]] = Field(None, alias="custom_field_values")

class RunbookRelationships(BaseModel):
    workspace: Optional[Relationship[JsonApiIdentifier]] = None
    folder: Optional[Relationship[JsonApiIdentifier]] = None
    runbook_type: Optional[Relationship[JsonApiIdentifier]] = Field(None, alias="runbook_type")
    author: Optional[Relationship[UserIdentifier]] = None
    current_version: Optional[Relationship[RunbookVersionIdentifier]] = Field(None, alias="current_version")

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
        return_model = func.__annotations__['return']
    except KeyError:
        # No return annotation, so we can't do anything
        return func

    # Check if the annotation is a Pydantic model class
    if inspect.isclass(return_model) and issubclass(return_model, BaseModel):
        # Generate the schema from the discovered model and replace the placeholder
        schema_string = return_model.schema_json(indent=4)
        func.__doc__ = func.__doc__.replace(placeholder, schema_string)

    return func