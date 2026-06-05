from sqlalchemy import (
    Column,
    Integer,
    UUID,
    String,
    ForeignKey,
    DateTime
)

from datetime import datetime

from app.models.base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID)
    project_id = Column(UUID, ForeignKey("projects.id"))

    title = Column(String)

    created_at = Column(DateTime)