from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ProjectStatus = Literal["idle", "running", "paused", "completed"]


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    status: ProjectStatus = "idle"
    config: dict[str, Any] = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: ProjectStatus
    created_at: datetime
    config: dict[str, Any]


class EnvelopeMeta(BaseModel):
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class Envelope(BaseModel):
    data: Any
    error: str | None = None
    meta: EnvelopeMeta | None = None
