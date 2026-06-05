"""
Project API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.schemas import project as schemas

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
def list_projects(db: Session = Depends(get_db)):
    """List all projects."""
    return {"message": "List projects endpoint"}


@router.post("/")
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    return {"message": "Create project endpoint", "data": project}


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project."""
    return {"message": f"Get project {project_id} endpoint"}
