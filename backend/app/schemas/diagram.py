# app/schemas/diagram.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ── HTTP Response Schemas ─────────────────────────────────────────

class DiagramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    architecture_id: uuid.UUID
    mermaid_code: str
    version: int
    is_active: bool
    version_label: str | None
    created_at: datetime
    updated_at: datetime


class GenerateDiagramResponse(BaseModel):
    project_id: uuid.UUID
    project_status: str
    diagram: DiagramResponse
    message: str


class DiagramVersionsResponse(BaseModel):
    """All diagram versions for a project (newest first)."""
    project_id: uuid.UUID
    versions: list[DiagramResponse]


# ── Request Schemas ───────────────────────────────────────────────

class DiagramReviewRequest(BaseModel):
    feedback: str = Field(
        min_length=5,
        max_length=2000,
        examples=["Add a Redis cache node between API and database"],
    )