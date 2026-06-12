# app/models/chat.py
import uuid

from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MessageRole


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # Enforces 1:1 at DB level — one session per project
        index=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="chat_session",
        lazy="noload",
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="noload",
        order_by="Message.sequence_order",  # Always ordered correctly
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} project_id={self.project_id}>"


class Message(Base):
    __tablename__ = "messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="messagerole", create_type=True),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Explicit ordering — do NOT rely on created_at for chat ordering.
    # Async writes can land out of timestamp order.
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Token count stored for future context window management.
    # Null = not yet counted (counted lazily or by background job).
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} seq={self.sequence_order}>"