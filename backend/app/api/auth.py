from datetime import datetime
from typing import Dict, List, Optional

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.schemas import auth as schemas
from app.core import security
from app.core.database import SessionLocal
from app.models.user import User

logger = logging.getLogger("app.api.auth")


router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_clerk_email(payload: Dict[str, any]) -> Optional[str]:
    email = payload.get("email")
    if email:
        return email

    email_addresses = payload.get("email_addresses") or []
    if isinstance(email_addresses, list):
        for item in email_addresses:
            if isinstance(item, dict) and item.get("email_address"):
                return item.get("email_address")
    return None


def _extract_clerk_name(payload: Dict[str, any]) -> Optional[str]:
    name = payload.get("name") or payload.get("full_name")
    if name:
        return name

    first = payload.get("first_name")
    last = payload.get("last_name")
    if first or last:
        return " ".join(part for part in [first, last] if part)

    email = _extract_clerk_email(payload)
    if email:
        return email.split("@")[0]
    return None


def _extract_clerk_created_at(payload: Dict[str, any]) -> Optional[str]:
    created_at = payload.get("created_at") or payload.get("createdAt")
    if created_at:
        return str(created_at)
    return None


def hash_password(password: str) -> str:
    import hashlib
    import os
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + hashed.hex()


def verify_password(password: str, stored_value: str) -> bool:
    import hashlib
    salt_hex, hashed_hex = stored_value.split(":")
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hashed.hex() == hashed_hex


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.RegisterUser, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email,
        password=hashed_password,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=schemas.UserResponse)
def login(user: schemas.LoginUser, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not db_user.password or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return db_user


@router.get("/verify", response_model=schemas.ClerkVerifyResponse)
def verify_session(request: Request, db: Session = Depends(get_db)):
    payload = security.verify_clerk_request(request)

    email = _extract_clerk_email(payload)
    if not email:
        raise HTTPException(status_code=400, detail="Clerk payload did not contain an email")

    username = _extract_clerk_name(payload)
    created_at = _extract_clerk_created_at(payload) or datetime.utcnow().isoformat()
    updated_at = datetime.utcnow().isoformat()

    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        db_user = User(
            email=email,
            password=None,
            username=username,
            is_active=True,
            created_at=created_at,
            updated_at=updated_at,
        )
        db.add(db_user)
    else:
        db_user.username = username or db_user.username
        db_user.created_at = db_user.created_at or created_at
        db_user.updated_at = updated_at

    db.commit()
    db.refresh(db_user)

    logger.info("Clerk verify: synced user %s (email=%s) to local DB", db_user.id, db_user.email)

    return {
        "signed_in": True,
        "user": db_user,
        "payload": payload,
    }


@router.get("/users", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    """Development-only helper: list local users."""
    users = db.query(User).all()
    return users
