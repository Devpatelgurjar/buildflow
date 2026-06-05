from sqlalchemy import (
    Column,
    Integer,
    UUID,
    Text,
    ForeignKey,
    JSON,
    DateTime
)

from datetime import datetime

from app.models.base import Base


# class Diagram(Base):

#     __tablename__ = "diagrams"

#     id = Column(
#         Integer,
#         primary_key=True,
#         index=True
#     )

#     project_id = Column(
#         Integer,
#         ForeignKey("projects.id"),
#         nullable=False
#     )

#     diagram_json = Column(
#         JSON,
#         nullable=True
#     )

#     version = Column(
#         Integer,
#         default=1
#     )

#     created_at = Column(
#         DateTime,
#         default=datetime.utcnow
#     )

#     updated_at = Column(
#         DateTime,
#         default=datetime.utcnow
#     )

class Diagram(Base):
    __tablename__ = "diagrams"

    id = Column(UUID)

    project_id = Column(UUID)

    mermaid_code = Column(Text)

    svg_url = Column(Text)

    png_url = Column(Text)