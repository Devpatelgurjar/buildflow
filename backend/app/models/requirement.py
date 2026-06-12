# app/models/requirement.py
import uuid

from sqlalchemy import Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RequirementDraft(Base):
    __tablename__ = "requirement_drafts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # One active draft per project
        index=True,
    )

    # JSONB — structured requirements validated by Pydantic before storage.
    # Never trust raw AI output; always validate first.
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Future: allow re-generation, marking old ones inactive
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="requirement_draft",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<RequirementDraft id={self.id} project_id={self.project_id} v{self.version}>"