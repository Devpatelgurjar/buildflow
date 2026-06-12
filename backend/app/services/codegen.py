# app/services/codegen.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.ai.prompts.codegen import CODEGEN_SYSTEM_PROMPT, build_codegen_prompt
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.enums import ProjectStatus
from app.repositories.architecture import ArchitectureRepository
from app.repositories.codegen import CodegenRepository
from app.repositories.diagram import DiagramRepository
from app.repositories.project import ProjectRepository
from app.repositories.requirements import RequirementRepository
from app.schemas.chat import ContextMessage
from app.schemas.codegen import CodegenAIOutput, GeneratedCodeResponse, GenerateCodeResponse


class CodegenService:
    def __init__(self, db: AsyncSession, ai: AIProvider | None = None):
        self.db = db
        self.repo = CodegenRepository(db)
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.arch_repo = ArchitectureRepository(db)
        self.diagram_repo = DiagramRepository(db)
        self.ai = ai or get_ai_provider()

    async def generate_code(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> GenerateCodeResponse:
        # ── Guard ─────────────────────────────────────────────────
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        if project.status != ProjectStatus.DIAGRAM_READY:
            raise BadRequestException(
                f"Code can only be generated after diagram is approved. "
                f"Current status: {project.status.value}"
            )

        # ── Load all upstream artifacts ───────────────────────────
        req_draft = await self.req_repo.get_by_project(project_id)
        arch = await self.arch_repo.get_by_project(project_id)
        diagram = await self.diagram_repo.get_active(project_id)

        if not req_draft or not arch or not diagram:
            raise BadRequestException(
                "Requirements, architecture, and diagram must all exist before generating code."
            )

        # ── AI call ───────────────────────────────────────────────
        prompt = build_codegen_prompt(
            requirements=req_draft.content,
            architecture=arch.content,
            mermaid=diagram.mermaid_code,
        )

        validated: CodegenAIOutput = await self.ai.complete_structured(
            messages=[ContextMessage(role="user", content=prompt)],
            response_schema=CodegenAIOutput,
            system_prompt=CODEGEN_SYSTEM_PROMPT,
        )

        # ── Store + transition ────────────────────────────────────
        code = await self.repo.create(
            project_id=project_id,
            diagram_id=diagram.id,
            artifacts=[a.model_dump() for a in validated.artifacts],
            language=validated.language,
            framework=validated.framework,
        )
        project.status = ProjectStatus.CODE_READY
        await self.db.flush()
        await self.db.refresh(project)

        return GenerateCodeResponse(
            project_id=project.id,
            project_status=project.status.value,
            generated_code=GeneratedCodeResponse.model_validate(code),
            message=f"Code generated successfully. {len(validated.artifacts)} files created.",
        )

    async def get_code(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> GeneratedCodeResponse:
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        code = await self.repo.get_by_project(project_id)
        if not code:
            raise NotFoundException("Generated code", str(project_id))
        return GeneratedCodeResponse.model_validate(code)