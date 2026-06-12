# app/db/base.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this base.

    Provides:
    - UUID primary key (PostgreSQL native UUID type)
    - created_at / updated_at audit timestamps (timezone-aware)

    Convention:
    - __tablename__ must be explicitly set on every subclass.
    - All timestamps stored as UTC.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

from app.models.user import User
from app.models.project import Project
from app.models.chat import ChatSession, Message