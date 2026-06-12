import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr,ConfigDict


class RegisterUser(BaseModel):
    email: EmailStr
    password: str
    username: str
    is_active: bool
    created_at: str
    updated_at: str


class LoginUser(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ClerkVerifyResponse(BaseModel):
    signed_in: bool
    user: UserResponse
    payload: Dict[str, Any]
