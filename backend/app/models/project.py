# app/models/project.py
import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        default=ProjectStatus.IDEA,
        nullable=False,
        index=True,
    )

    # Relationships — loaded lazily by default; use selectinload in queries
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="projects",
        lazy="noload",
    )

    chat_session: Mapped["ChatSession"] = relationship(  # noqa: F821
        "ChatSession",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    requirement_draft: Mapped["RequirementDraft"] = relationship(  # noqa: F821
        "RequirementDraft",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="noload",
    )

    architecture: Mapped["Architecture"] = relationship(  # noqa: F821
        "Architecture", 
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="noload",
    )

    diagrams: Mapped[list["Diagram"]] = relationship(  # noqa: F821
        "Diagram",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    generated_code: Mapped[list["GeneratedCode"]] = relationship(  # noqa: F821
        "GeneratedCode",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} title={self.title} status={self.status}>"