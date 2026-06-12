# app/repositories/requirement.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import RequirementDraft


class RequirementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project_id: uuid.UUID, content: dict) -> RequirementDraft:
        draft = RequirementDraft(
            project_id=project_id,
            content=content,
            version=1,
            is_active=True,
        )
        self.db.add(draft)
        await self.db.flush()
        await self.db.refresh(draft)
        return draft

    async def get_by_project(self, project_id: uuid.UUID) -> RequirementDraft | None:
        result = await self.db.execute(
            select(RequirementDraft).where(
                RequirementDraft.project_id == project_id,
                RequirementDraft.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()