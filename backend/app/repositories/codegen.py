# app/repositories/codegen.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.codegen import GeneratedCode


class CodegenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: uuid.UUID,
        diagram_id: uuid.UUID | None,
        artifacts: list,
        language: str,
        framework: str,
    ) -> GeneratedCode:
        code = GeneratedCode(
            project_id=project_id,
            diagram_id=diagram_id,
            artifacts=artifacts,
            language=language,
            framework=framework,
        )
        self.db.add(code)
        await self.db.flush()
        await self.db.refresh(code)
        return code

    async def get_by_project(self, project_id: uuid.UUID) -> GeneratedCode | None:
        result = await self.db.execute(
            select(GeneratedCode).where(GeneratedCode.project_id == project_id)
        )
        return result.scalar_one_or_none()