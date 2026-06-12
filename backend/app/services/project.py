# app/services/project.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    InvalidStateTransitionException,
)
from app.models.enums import ProjectStatus
from app.models.project import Project
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.pagination import PaginatedResponse, PaginationParams

VALID_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.IDEA:               {ProjectStatus.DISCUSSION},
    ProjectStatus.DISCUSSION:         {ProjectStatus.REQUIREMENTS_READY, ProjectStatus.ARCHIVED},
    ProjectStatus.REQUIREMENTS_READY: {ProjectStatus.ARCHITECTURE_READY, ProjectStatus.ARCHIVED},
    ProjectStatus.ARCHITECTURE_READY: {ProjectStatus.DIAGRAM_READY, ProjectStatus.ARCHIVED},
    ProjectStatus.DIAGRAM_READY:      {ProjectStatus.DIAGRAM_READY, ProjectStatus.CODE_READY, ProjectStatus.ARCHIVED},
    ProjectStatus.CODE_READY:         {ProjectStatus.ARCHIVED},
    ProjectStatus.ARCHIVED:           set(),
}


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)

    async def _get_owned_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        project = await self.repo.get_by_id(project_id)
        if project is None:
            raise NotFoundException("Project", str(project_id))
        if project.user_id != user_id:
            raise ForbiddenException("You do not own this project")
        return project

    def _assert_transition(self, project: Project, target: ProjectStatus, action: str) -> None:
        allowed = VALID_TRANSITIONS.get(project.status, set())
        if target not in allowed:
            raise InvalidStateTransitionException(
                current_state=project.status.value,
                required_state=target.value,
                action=action,
            )

    async def create_project(self, user_id: uuid.UUID, payload: ProjectCreate) -> Project:
        """
        Creates project (IDEA → DISCUSSION) and initializes chat session.
        Both happen in the same DB transaction via flush().
        """
        # Create project record
        project = await self.repo.create(
            user_id=user_id,
            title=payload.title,
            description=payload.description,
        )

        # Initialize chat session (import here to avoid circular import at module load)
        from app.services.chat import ChatService
        chat_service = ChatService(self.db)
        await chat_service.initialize_session(
            project_id=project.id,
            project_title=payload.title,
            project_description=payload.description,
        )

        # Advance state: IDEA → DISCUSSION
        project = await self.repo.update_status(project, ProjectStatus.DISCUSSION)
        return project

    async def get_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        return await self._get_owned_project(project_id, user_id)

    async def list_projects(self, user_id: uuid.UUID, pagination: PaginationParams) -> PaginatedResponse:
        projects, total = await self.repo.list_by_user(
            user_id=user_id,
            offset=pagination.offset,
            limit=pagination.limit,
        )
        return PaginatedResponse(items=projects, total=total, page=pagination.page, page_size=pagination.page_size)

    async def update_project(self, project_id: uuid.UUID, user_id: uuid.UUID, payload: ProjectUpdate) -> Project:
        project = await self._get_owned_project(project_id, user_id)
        if project.status in {ProjectStatus.CODE_READY, ProjectStatus.ARCHIVED}:
            raise ForbiddenException("Project cannot be edited in its current state")
        return await self.repo.update(project, title=payload.title, description=payload.description)

    async def archive_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        project = await self._get_owned_project(project_id, user_id)
        self._assert_transition(project, ProjectStatus.ARCHIVED, "archive")
        return await self.repo.archive(project)

    async def delete_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        project = await self._get_owned_project(project_id, user_id)
        await self.repo.delete(project)

    async def transition_to(self, project_id: uuid.UUID, user_id: uuid.UUID, target: ProjectStatus, action: str) -> Project:
        project = await self._get_owned_project(project_id, user_id)
        self._assert_transition(project, target, action)
        return await self.repo.update_status(project, target)

    async def assert_status(self, project: Project, required: ProjectStatus, action: str) -> None:
        if project.status != required:
            raise InvalidStateTransitionException(
                current_state=project.status.value,
                required_state=required.value,
                action=action,
            )