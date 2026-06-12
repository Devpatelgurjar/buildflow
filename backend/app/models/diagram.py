# app/models/diagram.py
import uuid

from sqlalchemy import Integer, Boolean, Text, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Diagram(Base):
    __tablename__ = "diagrams"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    architecture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("architectures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Mermaid diagram source code
    mermaid_code: Mapped[str] = mapped_column(Text, nullable=False)

    # Version increments on each review + regeneration
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Only one diagram is "active" (latest approved) at a time
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Optional label for the version (e.g. "Added Redis Cache")
    version_label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="diagrams",
        lazy="noload",
    )

    architecture: Mapped["Architecture"] = relationship(
        "Architecture",
        back_populates="diagrams",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Diagram id={self.id} project_id={self.project_id} v{self.version}>"