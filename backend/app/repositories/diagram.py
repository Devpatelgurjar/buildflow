# app/repositories/diagram.py
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagram import Diagram


class DiagramRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _next_version(self, project_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.max(Diagram.version)).where(Diagram.project_id == project_id)
        )
        current = result.scalar_one_or_none()
        return (current or 0) + 1

    async def _deactivate_all(self, project_id: uuid.UUID) -> None:
        """Mark all existing diagrams inactive before inserting a new active one."""
        await self.db.execute(
            update(Diagram)
            .where(Diagram.project_id == project_id)
            .values(is_active=False)
        )

    async def create(
        self,
        project_id: uuid.UUID,
        architecture_id: uuid.UUID,
        mermaid_code: str,
        version_label: str | None = None,
    ) -> Diagram:
        await self._deactivate_all(project_id)
        version = await self._next_version(project_id)
        diagram = Diagram(
            project_id=project_id,
            architecture_id=architecture_id,
            mermaid_code=mermaid_code,
            version=version,
            is_active=True,
            version_label=version_label,
        )
        self.db.add(diagram)
        await self.db.flush()
        await self.db.refresh(diagram)
        return diagram

    async def get_active(self, project_id: uuid.UUID) -> Diagram | None:
        result = await self.db.execute(
            select(Diagram).where(
                Diagram.project_id == project_id,
                Diagram.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def list_versions(self, project_id: uuid.UUID) -> list[Diagram]:
        result = await self.db.execute(
            select(Diagram)
            .where(Diagram.project_id == project_id)
            .order_by(Diagram.version.desc())
        )
        return list(result.scalars().all())
    