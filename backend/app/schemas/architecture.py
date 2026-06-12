# app/schemas/architecture.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ── AI Output Schema ──────────────────────────────────────────────

class ServiceComponent(BaseModel):
    name: str
    responsibility: str
    technology: str


class APIDesign(BaseModel):
    style: str
    versioning: str
    auth: str
    realtime: str


class DeploymentConfig(BaseModel):
    strategy: str
    ci_cd: str
    monitoring: str


class ArchitectureAIOutput(BaseModel):
    """Validates raw AI output before DB storage."""
    overview: str
    services: list[ServiceComponent] = Field(min_length=1)
    database_entities: list[str] = Field(min_length=1)
    api_design: APIDesign
    deployment: DeploymentConfig


# ── HTTP Response Schemas ─────────────────────────────────────────

class ArchitectureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    content: dict
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GenerateArchitectureResponse(BaseModel):
    project_id: uuid.UUID
    project_status: str
    architecture: ArchitectureResponse
    message: str


# ── Request Schemas ───────────────────────────────────────────────

class ArchitectureReviewRequest(BaseModel):
    feedback: str = Field(
        min_length=5,
        max_length=2000,
        examples=["Add a Redis cache layer between the API and the database"],
    )