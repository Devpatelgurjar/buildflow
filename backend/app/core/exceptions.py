# app/core/exceptions.py
from fastapi import HTTPException, status


# ─────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────

class BuildFlowException(Exception):
    """Root exception for all application errors."""
    pass


# ─────────────────────────────────────────────
# HTTP Exceptions (raised in routes/services)
# ─────────────────────────────────────────────

class NotFoundException(HTTPException):
    def __init__(self, resource: str = "Resource", resource_id: str | None = None):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} '{resource_id}' not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnprocessableEntityException(HTTPException):
    def __init__(self, detail: str = "Unprocessable entity"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


# ─────────────────────────────────────────────
# Domain-specific: Workflow / State Machine
# ─────────────────────────────────────────────

class InvalidStateTransitionException(HTTPException):
    """
    Raised when a workflow action is attempted on a project
    that is not in the required state.

    Example: Generating architecture before requirements exist.
    """
    def __init__(self, current_state: str, required_state: str, action: str):
        detail = (
            f"Cannot perform '{action}': "
            f"project is in '{current_state}' state, "
            f"but '{required_state}' is required."
        )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class AIProviderException(BuildFlowException):
    """
    Raised when an AI provider call fails.
    Caught at the service layer and converted to HTTP 502.
    """
    def __init__(self, provider: str, detail: str):
        self.provider = provider
        self.detail = detail
        super().__init__(f"AI provider '{provider}' error: {detail}")


class AIResponseValidationException(BuildFlowException):
    """
    Raised when the AI returns a response that fails
    Pydantic schema validation. Never trust AI output blindly.
    """
    def __init__(self, detail: str):
        super().__init__(f"AI response validation failed: {detail}")