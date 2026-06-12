# app/db/session.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ─────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────
# echo=False in production — set True only when DEBUG for SQL logging.
# pool_pre_ping=True: validates connections before checkout (handles DB restarts).
# pool_size / max_overflow: tune per workload. Defaults are conservative.

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent lazy-load errors after commit
    autocommit=False,
    autoflush=False,
)


# ─────────────────────────────────────────────
# FastAPI Dependency
# ─────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an async DB session per request.
    Rolls back on exception; always closes the session.

    Usage in routes:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()