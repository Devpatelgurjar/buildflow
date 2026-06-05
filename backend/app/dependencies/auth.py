"""
Authentication dependencies for FastAPI.
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
