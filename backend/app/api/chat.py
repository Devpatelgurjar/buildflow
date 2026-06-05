"""
Chat API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.schemas import chat as schemas

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """Send a chat message."""
    return {"message": "Chat endpoint", "response": "AI response placeholder"}


@router.get("/history")
def get_chat_history(db: Session = Depends(get_db)):
    """Get chat history."""
    return {"message": "Chat history endpoint"}
