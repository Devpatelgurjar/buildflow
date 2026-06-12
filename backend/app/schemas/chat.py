# app/schemas/chat.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import MessageRole


# ─────────────────────────────────────────────
# Request Schemas
# ─────────────────────────────────────────────

class MessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10_000,
        examples=["I want to add real-time order tracking with WebSockets"],
    )


# ─────────────────────────────────────────────
# Response Schemas
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    sequence_order: int
    token_count: int | None
    created_at: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ChatHistoryResponse(BaseModel):
    """Full paginated message history for a project's chat session."""
    session: ChatSessionResponse
    items: list[MessageResponse]
    pagination: dict


class SendMessageResponse(BaseModel):
    """Response after user sends a message — returns both user msg and AI reply."""
    user_message: MessageResponse
    assistant_message: MessageResponse


# ─────────────────────────────────────────────
# Internal — used by AI layer, not HTTP
# ─────────────────────────────────────────────

class ContextMessage(BaseModel):
    """
    Lightweight message format passed to AI providers.
    Strips DB-specific fields (id, timestamps) down to what LLMs need.
    """
    role: str   # "user" | "assistant" | "system"
    content: str