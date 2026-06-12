# app/services/requirements.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.ai.prompts.requirements import REQUIREMENTS_SYSTEM_PROMPT, build_requirements_prompt
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.enums import ProjectStatus
from app.repositories.project import ProjectRepository
from app.repositories.requirements import RequirementRepository
from app.schemas.requirement import RequirementsAIOutput, RequirementDraftResponse, FinalizeResponse
from app.services.chat import ChatService
from app.schemas.chat import ContextMessage


class RequirementService:
    """
    Handles the 'Finalize Discussion' action.

    Flow:
    1. Assert project is in DISCUSSION state
    2. Collect full chat history
    3. Send to AI with requirements extraction prompt
    4. Validate AI output through RequirementsAIOutput schema
    5. Store validated requirements in DB
    6. Transition project to REQUIREMENTS_READY
    """

    def __init__(self, db: AsyncSession, ai: AIProvider | None = None):
        self.db = db
        self.repo = RequirementRepository(db)
        self.project_repo = ProjectRepository(db)
        self.chat_service = ChatService(db, ai)
        self.ai = ai or get_ai_provider()

    async def finalize_discussion(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> FinalizeResponse:
        # ── 1. Ownership + state guard ────────────────────────────
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        if project.status != ProjectStatus.DISCUSSION:
            raise BadRequestException(
                f"Can only finalize during DISCUSSION phase. "
                f"Current status: {project.status.value}"
            )

        # ── 2. Collect full chat history ──────────────────────────
        context: list[ContextMessage] = await self.chat_service.get_full_context_for_ai(project_id)

        if not context:
            raise BadRequestException(
                "No discussion found. Have at least one conversation before finalizing."
            )

        # ── 3. Build prompt with project context ──────────────────
        intro = build_requirements_prompt(project.title, project.description)
        messages_for_ai = [
            ContextMessage(role="user", content=intro),
            *[m for m in context if m.role != "system"],  # Append chat history
        ]

        # ── 4. Call AI — structured output validated by Pydantic ──
        validated: RequirementsAIOutput = await self.ai.complete_structured(
            messages=messages_for_ai,
            response_schema=RequirementsAIOutput,
            system_prompt=REQUIREMENTS_SYSTEM_PROMPT,
        )

        # ── 5. Store validated requirements ───────────────────────
        draft = await self.repo.create(
            project_id=project_id,
            content=validated.model_dump(),
        )

        # ── 6. Transition state ───────────────────────────────────
        project.status = ProjectStatus.REQUIREMENTS_READY
        await self.db.flush()
        await self.db.refresh(project)

        return FinalizeResponse(
            project_id=project.id,
            project_status=project.status.value,
            requirement_draft=RequirementDraftResponse.model_validate(draft),
            message="Discussion finalized. Requirements have been generated successfully.",
        )

    async def get_requirements(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RequirementDraftResponse:
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        draft = await self.repo.get_by_project(project_id)
        if not draft:
            raise NotFoundException("Requirements", str(project_id))

        return RequirementDraftResponse.model_validate(draft)