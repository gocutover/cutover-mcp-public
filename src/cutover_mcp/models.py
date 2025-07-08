from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CutoverApiError(Exception):
    """Custom exception for Cutover API errors."""
    def __init__(self, message: str, status_code: int = None, details: List[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or []

class BaseAttributes(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class BaseResource(BaseModel):
    id: str
    type: str

class Runbook(BaseResource):
    attributes: BaseAttributes

class Task(BaseResource):
    attributes: BaseAttributes

class Workspace(BaseResource):
    attributes: BaseAttributes

class ActionLog(BaseResource):
    class ActionLogAttributes(BaseModel):
        action: str
        details: Optional[Dict[str, Any]] = None
        created_at: str = Field(alias="createdAt")

    attributes: ActionLogAttributes
