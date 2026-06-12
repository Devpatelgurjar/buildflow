# app/core/security.py
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = PasswordHash.recommended()


# ─────────────────────────────────────────────
# Password
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return password_hash.verify(plain, hashed)  
    except ValueError:
        # Handle invalid hash format
        return False


# ─────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────

def create_access_token(subject: str) -> str:
    """
    Create a JWT access token.
    subject: typically the user's UUID as string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """
    Decode and validate a JWT token.
    Returns the subject (user UUID) or raises UnauthorizedException.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        subject: str | None = payload.get("sub")
        if subject is None:
            raise UnauthorizedException("Token missing subject")
        return subject
    except JWTError:
        raise UnauthorizedException("Invalid or expired token")