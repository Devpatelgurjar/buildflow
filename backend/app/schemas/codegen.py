# app/schemas/codegen.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ── AI Output Schema ──────────────────────────────────────────────

class CodeArtifact(BaseModel):
    filename: str
    language: str
    description: str
    content: str


class CodegenAIOutput(BaseModel):
    """Validates raw AI output before DB storage."""
    language: str
    framework: str
    artifacts: list[CodeArtifact] = Field(min_length=1)
    setup_instructions: str


# ── HTTP Response Schemas ─────────────────────────────────────────

class GeneratedCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    diagram_id: uuid.UUID | None
    artifacts: list
    language: str
    framework: str
    created_at: datetime
    updated_at: datetime


class GenerateCodeResponse(BaseModel):
    project_id: uuid.UUID
    project_status: str
    generated_code: GeneratedCodeResponse
    message: str