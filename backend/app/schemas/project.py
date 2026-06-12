# app/schemas/project.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import ProjectStatus


# ─────────────────────────────────────────────
# Request Schemas
# ─────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=255,
        examples=["Food Delivery App"],
    )
    description: str = Field(
        min_length=10,
        max_length=5000,
        examples=["I want to build a platform similar to Swiggy with real-time tracking."],
    )


class ProjectUpdate(BaseModel):
    """Partial update — all fields optional."""
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10, max_length=5000)


# ─────────────────────────────────────────────
# Response Schemas
# ─────────────────────────────────────────────

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated project list."""
    items: list[ProjectResponse]
    pagination: dict


class ProjectStatusResponse(BaseModel):
    """Lightweight response for state-change operations."""
    id: uuid.UUID
    status: ProjectStatus
    message: str