"""
Chat schemas.
"""
from typing import Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    model: Optional[str] = None
