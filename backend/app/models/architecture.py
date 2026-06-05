from sqlalchemy import (
    Column,
    Integer,
    UUID,
    JSON,
    String,
    ForeignKey,
    DateTime
)

from datetime import datetime

from app.models.base import Base

class Architecture(Base):
    __tablename__ = "architectures"

    id = Column(UUID)

    project_id = Column(UUID)

    architecture_json = Column(JSON)

    created_at = Column(DateTime)