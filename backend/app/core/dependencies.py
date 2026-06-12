# app/core/dependencies.py
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException, NotFoundException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from sqlalchemy import select

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that:
    1. Extracts Bearer token from Authorization header
    2. Decodes and validates JWT
    3. Loads user from DB
    4. Raises 401 if anything fails

    Usage in routes:
        current_user: User = Depends(get_current_user)
    """
    if credentials is None:
        raise UnauthorizedException("Authorization header missing")

    user_id_str = decode_access_token(credentials.credentials)

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid token subject")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("User account is inactive")

    return user