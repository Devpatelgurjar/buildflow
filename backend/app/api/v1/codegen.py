# app/api/v1/codegen.py
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.codegen import GeneratedCodeResponse, GenerateCodeResponse
from app.services.codegen import CodegenService

router = APIRouter(prefix="/projects", tags=["Code Generation"])


def get_service(db: AsyncSession = Depends(get_db), ai: AIProvider = Depends(get_ai_provider)):
    return CodegenService(db=db, ai=ai)


@router.post(
    "/{project_id}/code",
    response_model=GenerateCodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate code from approved architecture and diagram",
    description=(
        "Reads requirements, architecture, and active diagram. "
        "Generates code artifacts and transitions project to CODE_READY."
    ),
)
async def generate_code(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CodegenService = Depends(get_service),
) -> GenerateCodeResponse:
    return await service.generate_code(project_id, current_user.id)


@router.get(
    "/{project_id}/code",
    response_model=GeneratedCodeResponse,
    summary="Get generated code artifacts",
)
async def get_code(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CodegenService = Depends(get_service),
) -> GeneratedCodeResponse:
    return await service.get_code(project_id, current_user.id)