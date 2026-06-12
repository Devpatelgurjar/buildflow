# app/models/codegen.py
import uuid

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeneratedCode(Base):
    __tablename__ = "generated_code"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    diagram_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagrams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Array of {filename, language, description, content} objects
    artifacts: Mapped[list] = mapped_column(JSONB, nullable=False)

    language: Mapped[str] = mapped_column(String(50), nullable=False, default="python")
    framework: Mapped[str] = mapped_column(String(50), nullable=False, default="fastapi")

    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="generated_code",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<GeneratedCode id={self.id} project_id={self.project_id}>"