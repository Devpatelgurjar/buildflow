# app/services/diagram.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.ai.prompts.diagram import (
    DIAGRAM_SYSTEM_PROMPT,
    DIAGRAM_REVIEW_SYSTEM_PROMPT,
    build_diagram_prompt,
    build_diagram_review_prompt,
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.enums import ProjectStatus
from app.repositories.architecture import ArchitectureRepository
from app.repositories.diagram import DiagramRepository
from app.repositories.project import ProjectRepository
from app.schemas.chat import ContextMessage
from app.schemas.diagram import (
    DiagramResponse,
    GenerateDiagramResponse,
    DiagramVersionsResponse,
)


class DiagramService:
    def __init__(self, db: AsyncSession, ai: AIProvider | None = None):
        self.db = db
        self.repo = DiagramRepository(db)
        self.project_repo = ProjectRepository(db)
        self.arch_repo = ArchitectureRepository(db)
        self.ai = ai or get_ai_provider()

    async def generate_diagram(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> GenerateDiagramResponse:
        # ── Guard ─────────────────────────────────────────────────
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        if project.status != ProjectStatus.ARCHITECTURE_READY:
            raise BadRequestException(
                f"Diagram can only be generated after architecture is ready. "
                f"Current status: {project.status.value}"
            )

        # ── Load architecture ─────────────────────────────────────
        arch = await self.arch_repo.get_by_project(project_id)
        if not arch:
            raise NotFoundException("Architecture", str(project_id))

        # ── AI call — returns raw Mermaid text ────────────────────
        prompt = build_diagram_prompt(arch.content)
        mermaid_code = await self.ai.complete(
            messages=[ContextMessage(role="user", content=prompt)],
            system_prompt=DIAGRAM_SYSTEM_PROMPT,
        )
        mermaid_code = mermaid_code.strip()

        # ── Store + transition ────────────────────────────────────
        diagram = await self.repo.create(
            project_id=project_id,
            architecture_id=arch.id,
            mermaid_code=mermaid_code,
            version_label="Initial generation",
        )
        project.status = ProjectStatus.DIAGRAM_READY
        await self.db.flush()
        await self.db.refresh(project)

        return GenerateDiagramResponse(
            project_id=project.id,
            project_status=project.status.value,
            diagram=DiagramResponse.model_validate(diagram),
            message="Diagram generated successfully.",
        )

    async def review_diagram(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        feedback: str,
    ) -> GenerateDiagramResponse:
        """
        User requests a change (e.g. "Add Redis cache").
        Creates a new diagram version; project stays in DIAGRAM_READY.
        """
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        if project.status != ProjectStatus.DIAGRAM_READY:
            raise BadRequestException(
                f"Diagram review requires DIAGRAM_READY status. "
                f"Current status: {project.status.value}"
            )

        arch = await self.arch_repo.get_by_project(project_id)
        current_diagram = await self.repo.get_active(project_id)
        if not arch or not current_diagram:
            raise NotFoundException("Diagram or Architecture", str(project_id))

        # ── AI call ───────────────────────────────────────────────
        prompt = build_diagram_review_prompt(
            current_mermaid=current_diagram.mermaid_code,
            current_architecture=arch.content,
            user_feedback=feedback,
        )
        raw_response = await self.ai.complete(
            messages=[ContextMessage(role="user", content=prompt)],
            system_prompt=DIAGRAM_REVIEW_SYSTEM_PROMPT,
        )

        # Extract Mermaid code — it follows after explanation text
        mermaid_code = self._extract_mermaid(raw_response)

        # ── New version ───────────────────────────────────────────
        new_diagram = await self.repo.create(
            project_id=project_id,
            architecture_id=arch.id,
            mermaid_code=mermaid_code,
            version_label=feedback[:100],  # Use feedback as label (truncated)
        )

        return GenerateDiagramResponse(
            project_id=project.id,
            project_status=project.status.value,
            diagram=DiagramResponse.model_validate(new_diagram),
            message=f"Diagram updated. Version {new_diagram.version} created.",
        )

    async def get_diagram(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> DiagramResponse:
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        diagram = await self.repo.get_active(project_id)
        if not diagram:
            raise NotFoundException("Diagram", str(project_id))
        return DiagramResponse.model_validate(diagram)

    async def list_versions(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> DiagramVersionsResponse:
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        versions = await self.repo.list_versions(project_id)
        return DiagramVersionsResponse(
            project_id=project_id,
            versions=[DiagramResponse.model_validate(d) for d in versions],
        )

    def _extract_mermaid(self, raw: str) -> str:
        """
        Extract Mermaid code from AI response that may contain
        an explanation paragraph before the diagram.
        Looks for 'graph TD' or 'graph LR' as the start marker.
        """
        raw = raw.strip()
        # Strip markdown fences
        raw = raw.replace("```mermaid", "").replace("```", "").strip()

        for marker in ("graph TD", "graph LR", "graph BT", "flowchart TD"):
            idx = raw.find(marker)
            if idx != -1:
                return raw[idx:].strip()

        # If no marker found, return as-is (mock provider returns clean code)
        return raw