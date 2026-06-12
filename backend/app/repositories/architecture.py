# app/repositories/architecture.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import Architecture


class ArchitectureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project_id: uuid.UUID, content: dict) -> Architecture:
        arch = Architecture(project_id=project_id, content=content, version=1, is_active=True)
        self.db.add(arch)
        await self.db.flush()
        await self.db.refresh(arch)
        return arch

    async def get_by_project(self, project_id: uuid.UUID) -> Architecture | None:
        result = await self.db.execute(
            select(Architecture).where(
                Architecture.project_id == project_id,
                Architecture.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def update_content(self, arch: Architecture, content: dict) -> Architecture:
        arch.content = content
        arch.version += 1
        await self.db.flush()
        await self.db.refresh(arch)
        return arch