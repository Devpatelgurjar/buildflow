# app/api/v1/diagram.py
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.diagram import (
    DiagramResponse,
    GenerateDiagramResponse,
    DiagramVersionsResponse,
    DiagramReviewRequest,
)
from app.services.diagram import DiagramService

router = APIRouter(prefix="/projects", tags=["Diagram"])


def get_service(db: AsyncSession = Depends(get_db), ai: AIProvider = Depends(get_ai_provider)):
    return DiagramService(db=db, ai=ai)


@router.post(
    "/{project_id}/diagram",
    response_model=GenerateDiagramResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Mermaid diagram from architecture",
)
async def generate_diagram(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DiagramService = Depends(get_service),
) -> GenerateDiagramResponse:
    return await service.generate_diagram(project_id, current_user.id)


@router.get(
    "/{project_id}/diagram",
    response_model=DiagramResponse,
    summary="Get the active diagram",
)
async def get_diagram(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DiagramService = Depends(get_service),
) -> DiagramResponse:
    return await service.get_diagram(project_id, current_user.id)


@router.post(
    "/{project_id}/diagram/review",
    response_model=GenerateDiagramResponse,
    status_code=status.HTTP_200_OK,
    summary="Review diagram — request changes and regenerate",
    description="User provides feedback; AI updates architecture and creates a new diagram version.",
)
async def review_diagram(
    project_id: uuid.UUID,
    payload: DiagramReviewRequest,
    current_user: User = Depends(get_current_user),
    service: DiagramService = Depends(get_service),
) -> GenerateDiagramResponse:
    return await service.review_diagram(project_id, current_user.id, payload.feedback)


@router.get(
    "/{project_id}/diagram/versions",
    response_model=DiagramVersionsResponse,
    summary="List all diagram versions",
)
async def list_versions(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DiagramService = Depends(get_service),
) -> DiagramVersionsResponse:
    return await service.list_versions(project_id, current_user.id)