# app/schemas/requirement.py
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ─────────────────────────────────────────────
# AI Output Schema — validates raw AI response
# NEVER store to DB without passing through this first
# ─────────────────────────────────────────────

class FunctionalRequirement(BaseModel):
    id: str = Field(examples=["FR-001"])
    category: str
    title: str
    description: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]


class NonFunctionalRequirement(BaseModel):
    category: str
    description: str


class RequirementsAIOutput(BaseModel):
    """
    Pydantic schema that AI output must satisfy before being stored.
    If AI returns garbage, this raises AIResponseValidationException —
    never persists invalid data.
    """
    project_summary: str
    functional_requirements: list[FunctionalRequirement] = Field(min_length=1)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(min_length=1)
    out_of_scope: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# HTTP Response Schemas
# ─────────────────────────────────────────────

class RequirementDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    content: dict        # The full validated requirements JSON
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FinalizeResponse(BaseModel):
    """Returned when user clicks 'Finalize Discussion'."""
    project_id: uuid.UUID
    project_status: str
    requirement_draft: RequirementDraftResponse
    message: str