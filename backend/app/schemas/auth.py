from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr


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
    id: int
    email: EmailStr
    username: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class ClerkVerifyResponse(BaseModel):
    signed_in: bool
    user: UserResponse
    payload: Dict[str, Any]
