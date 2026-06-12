# app/api/v1/chat.py
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import (
    MessageCreate,
    MessageResponse,
    ChatHistoryResponse,
    ChatSessionResponse,
    SendMessageResponse,
)
from app.services.chat import ChatService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/projects", tags=["Chat"])


def get_chat_service(
    db: AsyncSession = Depends(get_db),
    ai: AIProvider = Depends(get_ai_provider),
) -> ChatService:
    return ChatService(db=db, ai=ai)


# ── GET /projects/{id}/session ────────────────────────────────────
@router.get(
    "/{project_id}/session",
    response_model=ChatSessionResponse,
    summary="Get the chat session for a project",
)
async def get_session(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionResponse:
    session = await service.get_session(project_id, current_user.id)
    return ChatSessionResponse.model_validate(session)


# ── GET /projects/{id}/messages ───────────────────────────────────
@router.get(
    "/{project_id}/messages",
    response_model=ChatHistoryResponse,
    summary="Get paginated chat history for a project",
    description="Returns user and assistant messages. System prompts are excluded.",
)
async def get_messages(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    service: ChatService = Depends(get_chat_service),
) -> ChatHistoryResponse:
    session = await service.get_session(project_id, current_user.id)
    paginated = await service.get_history(
        project_id=project_id,
        user_id=current_user.id,
        pagination=pagination,
    )
    result = paginated.to_dict()
    return ChatHistoryResponse(
        session=ChatSessionResponse.model_validate(session),
        items=[MessageResponse.model_validate(m) for m in result["items"]],
        pagination=result["pagination"],
    )


# ── POST /projects/{id}/messages ──────────────────────────────────
@router.post(
    "/{project_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in the project discussion",
    description=(
        "Sends a user message and returns both the user message "
        "and the AI assistant's response in a single call."
    ),
)
async def send_message(
    project_id: uuid.UUID,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> SendMessageResponse:
    return await service.send_message(
        project_id=project_id,
        user_id=current_user.id,
        content=payload.content,
    )