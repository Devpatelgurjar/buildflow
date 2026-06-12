# app/services/architecture.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.ai.prompts.architecture import (
    ARCHITECTURE_SYSTEM_PROMPT,
    build_architecture_prompt,
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.enums import ProjectStatus
from app.repositories.architecture import ArchitectureRepository
from app.repositories.project import ProjectRepository
from app.repositories.requirements import RequirementRepository
from app.schemas.architecture import (
    ArchitectureAIOutput,
    ArchitectureResponse,
    GenerateArchitectureResponse,
)


class ArchitectureService:
    def __init__(self, db: AsyncSession, ai: AIProvider | None = None):
        self.db = db
        self.repo = ArchitectureRepository(db)
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.ai = ai or get_ai_provider()

    async def generate_architecture(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> GenerateArchitectureResponse:
        # ── Guard ─────────────────────────────────────────────────
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        if project.status != ProjectStatus.REQUIREMENTS_READY:
            raise BadRequestException(
                f"Architecture can only be generated after requirements are ready. "
                f"Current status: {project.status.value}"
            )

        # ── Load requirements ─────────────────────────────────────
        req_draft = await self.req_repo.get_by_project(project_id)
        if not req_draft:
            raise NotFoundException("Requirements", str(project_id))

        # ── AI call ───────────────────────────────────────────────
        from app.schemas.chat import ContextMessage
        prompt = build_architecture_prompt(req_draft.content)

        validated: ArchitectureAIOutput = await self.ai.complete_structured(
            messages=[ContextMessage(role="user", content=prompt)],
            response_schema=ArchitectureAIOutput,
            system_prompt=ARCHITECTURE_SYSTEM_PROMPT,
        )

        # ── Store + transition ────────────────────────────────────
        arch = await self.repo.create(
            project_id=project_id,
            content=validated.model_dump(),
        )
        project.status = ProjectStatus.ARCHITECTURE_READY
        await self.db.flush()
        await self.db.refresh(project)

        return GenerateArchitectureResponse(
            project_id=project.id,
            project_status=project.status.value,
            architecture=ArchitectureResponse.model_validate(arch),
            message="Architecture generated successfully.",
        )

    async def get_architecture(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ArchitectureResponse:
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        arch = await self.repo.get_by_project(project_id)
        if not arch:
            raise NotFoundException("Architecture", str(project_id))
        return ArchitectureResponse.model_validate(arch)