import os

from fastapi import HTTPException, Request
from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions, AuthStatus


def get_clerk_secret_key() -> str:
    secret_key = os.getenv("CLERK_SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "CLERK_SECRET_KEY is required for Clerk token verification. Set it in backend/.env or your environment."
        )
    return secret_key


def verify_clerk_request(request: Request) -> dict:
    secret_key = get_clerk_secret_key()
    frontend_url = os.getenv("CLERK_FRONTEND_URL")

    options = AuthenticateRequestOptions(
        secret_key=secret_key,
        authorized_parties=[frontend_url] if frontend_url else None,
        accepts_token=["any"],
    )

    auth_state = authenticate_request(request, options)
    if auth_state.status != AuthStatus.SIGNED_IN:
        raise HTTPException(
            status_code=401,
            detail=auth_state.message or "Unauthorized Clerk session",
        )

    return auth_state.payload or {}
