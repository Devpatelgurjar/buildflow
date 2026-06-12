# app/services/chat.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.ai.prompts.discussion import build_discussion_init_messages
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.chat import ChatSession, Message
from app.models.enums import MessageRole, ProjectStatus
from app.repositories.chat import ChatRepository
from app.repositories.project import ProjectRepository
from app.schemas.chat import ContextMessage, SendMessageResponse, MessageResponse
from app.utils.pagination import PaginatedResponse, PaginationParams


class ChatService:
    """
    Manages the chat lifecycle for a BuildFlow project.

    Responsibilities:
    - Initialize chat session + system prompt when project is created
    - Store user messages and AI responses with correct sequencing
    - Build context window for AI calls (full history or sliding window)
    - Guard: chat only active while project is in DISCUSSION state

    Does NOT:
    - Transition project state (ProjectService does that)
    - Call AI directly in finalize — that's RequirementService's job
    """

    def __init__(self, db: AsyncSession, ai: AIProvider | None = None):
        self.db = db
        self.repo = ChatRepository(db)
        self.project_repo = ProjectRepository(db)
        self.ai = ai or get_ai_provider()

    # ── Session Initialization ─────────────────────────────────────

    async def initialize_session(
        self,
        project_id: uuid.UUID,
        project_title: str,
        project_description: str,
    ) -> tuple[ChatSession, Message]:
        """
        Called immediately after project creation.
        Creates the ChatSession, injects system prompt + first user message,
        then gets the AI's opening response.

        Returns: (session, assistant_opening_message)
        """
        # Create session
        session = await self.repo.create_session(project_id=project_id)

        # Inject system prompt + initial user message
        init_messages = build_discussion_init_messages(project_title, project_description)
        await self.repo.create_messages_bulk(
            session_id=session.id,
            messages=[
                {"role": MessageRole.SYSTEM, "content": init_messages[0]["content"]},
                {"role": MessageRole.USER, "content": init_messages[1]["content"]},
            ],
        )

        # Get AI's opening response
        context = await self._build_context(session.id)
        ai_text = await self.ai.complete(
            messages=[m for m in context if m.role != "system"],
            system_prompt=next((m.content for m in context if m.role == "system"), None),
        )

        assistant_msg = await self.repo.create_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=ai_text,
        )

        return session, assistant_msg

    # ── Send Message ───────────────────────────────────────────────

    async def send_message(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> SendMessageResponse:
        """
        Handles a user message during the discussion phase:
        1. Validates project ownership and state
        2. Saves user message
        3. Builds context window
        4. Calls AI
        5. Saves AI response
        6. Returns both messages
        """
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        if project.status != ProjectStatus.DISCUSSION:
            raise BadRequestException(
                f"Chat is only active during DISCUSSION phase. "
                f"Current status: {project.status.value}"
            )

        session = await self.repo.get_session_by_project(project_id)
        if not session:
            raise NotFoundException("ChatSession for project", str(project_id))

        # Save user message
        user_msg = await self.repo.create_message(
            session_id=session.id,
            role=MessageRole.USER,
            content=content,
        )

        # Build context and call AI
        context = await self._build_context(session.id)
        system_prompt = next((m.content for m in context if m.role == "system"), None)
        chat_messages = [m for m in context if m.role != "system"]

        ai_text = await self.ai.complete(
            messages=chat_messages,
            system_prompt=system_prompt,
        )

        # Save assistant response
        assistant_msg = await self.repo.create_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=ai_text,
        )

        return SendMessageResponse(
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
        )

    # ── History ────────────────────────────────────────────────────

    async def get_history(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        pagination: PaginationParams,
    ) -> PaginatedResponse:
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        session = await self.repo.get_session_by_project(project_id)
        if not session:
            raise NotFoundException("ChatSession for project", str(project_id))

        messages, total = await self.repo.list_messages(
            session_id=session.id,
            offset=pagination.offset,
            limit=pagination.limit,
            exclude_system=True,  # Don't expose system prompts to users
        )

        return PaginatedResponse(
            items=messages,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_session(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChatSession:
        project = await self.project_repo.get_by_id_and_user(project_id, user_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        session = await self.repo.get_session_by_project(project_id)
        if not session:
            raise NotFoundException("ChatSession for project", str(project_id))
        return session

    # ── Context Window Builder ─────────────────────────────────────

    async def _build_context(
        self,
        session_id: uuid.UUID,
        max_messages: int = 40,
    ) -> list[ContextMessage]:
        """
        Constructs the message list sent to the AI provider.

        Strategy:
        - Always includes the system prompt (if present) at position 0
        - Uses a sliding window of the last `max_messages` non-system messages
          to stay within token limits
        - System message is extracted separately and passed as system_prompt
          to providers that handle it differently (e.g., Anthropic)

        Future extension: replace max_messages with token-budget-aware windowing
        using the stored token_count field on each Message.
        """
        all_messages = await self.repo.get_full_history(session_id)

        system_messages = [m for m in all_messages if m.role == MessageRole.SYSTEM]
        chat_messages = [m for m in all_messages if m.role != MessageRole.SYSTEM]

        # Sliding window — keep only last N chat messages
        windowed = chat_messages[-max_messages:]

        context: list[ContextMessage] = []

        # System prompt always first
        if system_messages:
            context.append(ContextMessage(
                role="system",
                content=system_messages[0].content,
            ))

        context.extend([
            ContextMessage(role=m.role.value, content=m.content)
            for m in windowed
        ])

        return context

    async def get_full_context_for_ai(
        self,
        project_id: uuid.UUID,
    ) -> list[ContextMessage]:
        """
        Public method called by RequirementService during finalize.
        Returns full chat history as ContextMessages for prompt assembly.
        """
        session = await self.repo.get_session_by_project(project_id)
        if not session:
            return []
        return await self._build_context(session.id, max_messages=200)