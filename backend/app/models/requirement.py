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

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(UUID)

    project_id = Column(UUID)

    functional_requirements = Column(JSON)

    non_functional_requirements = Column(JSON)

    assumptions = Column(JSON)

    created_at = Column(DateTime)