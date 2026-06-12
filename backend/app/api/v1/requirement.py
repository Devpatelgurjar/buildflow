# app/api/v1/requirement.py
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.requirement import FinalizeResponse, RequirementDraftResponse
from app.services.requirements import RequirementService

router = APIRouter(prefix="/projects", tags=["Requirements"])


def get_requirement_service(
    db: AsyncSession = Depends(get_db),
    ai: AIProvider = Depends(get_ai_provider),
) -> RequirementService:
    return RequirementService(db=db, ai=ai)


# ── POST /projects/{id}/finalize ──────────────────────────────────
@router.post(
    "/{project_id}/finalize",
    response_model=FinalizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalize discussion and generate requirements",
    description=(
        "Collects full chat history, sends to AI for structured requirements extraction, "
        "stores the result, and transitions project to REQUIREMENTS_READY."
    ),
)
async def finalize_discussion(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: RequirementService = Depends(get_requirement_service),
) -> FinalizeResponse:
    return await service.finalize_discussion(
        project_id=project_id,
        user_id=current_user.id,
    )


# ── GET /projects/{id}/requirements ───────────────────────────────
@router.get(
    "/{project_id}/requirements",
    response_model=RequirementDraftResponse,
    summary="Get generated requirements for a project",
)
async def get_requirements(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: RequirementService = Depends(get_requirement_service),
) -> RequirementDraftResponse:
    return await service.get_requirements(
        project_id=project_id,
        user_id=current_user.id,
    )