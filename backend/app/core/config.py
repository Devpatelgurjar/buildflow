"""
Configuration module for the application.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/buildflow"
    )
    
    # Clerk
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_FRONTEND_URL: str = os.getenv("CLERK_FRONTEND_URL", "")
    
    # Debug
    DEBUG_DB: bool = os.getenv("DEBUG_DB", "").lower() in ("1", "true", "yes")


settings = Settings()
