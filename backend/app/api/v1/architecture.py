# app/api/v1/architecture.py
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.architecture import ArchitectureResponse, GenerateArchitectureResponse
from app.services.architecture import ArchitectureService

router = APIRouter(prefix="/projects", tags=["Architecture"])


def get_service(db: AsyncSession = Depends(get_db), ai: AIProvider = Depends(get_ai_provider)):
    return ArchitectureService(db=db, ai=ai)


@router.post(
    "/{project_id}/architecture",
    response_model=GenerateArchitectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate architecture from requirements",
)
async def generate_architecture(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ArchitectureService = Depends(get_service),
) -> GenerateArchitectureResponse:
    return await service.generate_architecture(project_id, current_user.id)


@router.get(
    "/{project_id}/architecture",
    response_model=ArchitectureResponse,
    summary="Get the generated architecture",
)
async def get_architecture(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ArchitectureService = Depends(get_service),
) -> ArchitectureResponse:
    return await service.get_architecture(project_id, current_user.id)