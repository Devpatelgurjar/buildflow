# app/models/architecture.py
import uuid

from sqlalchemy import Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Architecture(Base):
    __tablename__ = "architectures"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Structured architecture: services, DB entities, API design, deployment
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="architecture",
        lazy="noload",
    )

    diagrams: Mapped[list["Diagram"]] = relationship(  # noqa: F821
        "Diagram",
        back_populates="architecture",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Architecture id={self.id} project_id={self.project_id} v{self.version}>"