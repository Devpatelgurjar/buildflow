from sqlalchemy import (
    Column,
    Integer,
    UUID,
    Text,
    String,
    ForeignKey,
    DateTime
)

from datetime import datetime

from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID)

    session_id = Column(
        UUID,
        ForeignKey("chat_sessions.id")
    )

    role = Column(String)

    content = Column(Text)

    created_at = Column(DateTime)