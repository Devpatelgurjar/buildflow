# database.py
# connects to db and creates sessions for use in the app

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Read DATABASE_URL from environment when available (helps local overrides and containers)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/buildflow",
)

# Enable SQL echo when DEBUG_DB env var is set (useful for development)
engine = create_engine(DATABASE_URL, echo=os.getenv("DEBUG_DB", "").lower() in ("1", "true", "yes"))

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)