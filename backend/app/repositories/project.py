# app/repositories/project.py
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.enums import ProjectStatus


class ProjectRepository:
    """
    Handles all DB operations for the Project model.

    Rules:
    - No business logic here — only DB queries.
    - No HTTP exceptions — raise plain Python exceptions if needed.
    - Always receive a db session; never create one internally.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Create ────────────────────────────────────────────────────

    async def create(
        self,
        user_id: uuid.UUID,
        title: str,
        description: str,
    ) -> Project:
        project = Project(
            user_id=user_id,
            title=title,
            description=description,
            status=ProjectStatus.IDEA,
        )
        self.db.add(project)
        await self.db.flush()  # Flush to get the generated ID before commit
        await self.db.refresh(project)
        return project

    # ── Read ──────────────────────────────────────────────────────

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Project | None:
        """Ownership-scoped fetch — primary guard for all project access."""
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        """Returns (projects, total_count) for pagination."""
        base_query = select(Project).where(
            Project.user_id == user_id,
            Project.status != ProjectStatus.ARCHIVED,
        )

        # Count query — avoids N+1 by running one extra COUNT
        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        # Data query with pagination
        result = await self.db.execute(
            base_query
            .order_by(Project.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        projects = list(result.scalars().all())

        return projects, total

    # ── Update ────────────────────────────────────────────────────

    async def update(
        self,
        project: Project,
        title: str | None = None,
        description: str | None = None,
    ) -> Project:
        if title is not None:
            project.title = title
        if description is not None:
            project.description = description
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update_status(
        self, project: Project, new_status: ProjectStatus
    ) -> Project:
        project.status = new_status
        await self.db.flush()
        await self.db.refresh(project)
        return project

    # ── Delete (soft via archive) ─────────────────────────────────

    async def archive(self, project: Project) -> Project:
        project.status = ProjectStatus.ARCHIVED
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        """Hard delete — cascades to all child records via FK constraints."""
        await self.db.delete(project)
        await self.db.flush()