# app/api/v1/project.py
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStatusResponse,
)
from app.services.project import ProjectService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


# ── POST /projects ────────────────────────────────────────────────
@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description=(
        "Creates a project and immediately opens it for discussion. "
        "A chat session is attached automatically."
    ),
)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = await service.create_project(
        user_id=current_user.id,
        payload=payload,
    )
    return ProjectResponse.model_validate(project)


# ── GET /projects ─────────────────────────────────────────────────
@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List all projects",
    description="Returns paginated list of the current user's active projects.",
)
async def list_projects(
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    paginated = await service.list_projects(
        user_id=current_user.id,
        pagination=pagination,
    )
    result = paginated.to_dict()
    result["items"] = [ProjectResponse.model_validate(p) for p in result["items"]]
    return ProjectListResponse(**result)


# ── GET /projects/{project_id} ────────────────────────────────────
@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project",
)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = await service.get_project(
        project_id=project_id,
        user_id=current_user.id,
    )
    return ProjectResponse.model_validate(project)


# ── PATCH /projects/{project_id} ──────────────────────────────────
@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project title or description",
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = await service.update_project(
        project_id=project_id,
        user_id=current_user.id,
        payload=payload,
    )
    return ProjectResponse.model_validate(project)


# ── POST /projects/{project_id}/archive ───────────────────────────
@router.post(
    "/{project_id}/archive",
    response_model=ProjectStatusResponse,
    summary="Archive a project",
)
async def archive_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectStatusResponse:
    project = await service.archive_project(
        project_id=project_id,
        user_id=current_user.id,
    )
    return ProjectStatusResponse(
        id=project.id,
        status=project.status,
        message="Project archived successfully",
    )


# ── DELETE /projects/{project_id} ─────────────────────────────────
@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a project",
    description="Hard delete — cascades to all chat, requirements, diagrams, and code.",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> None:
    await service.delete_project(
        project_id=project_id,
        user_id=current_user.id,
    )