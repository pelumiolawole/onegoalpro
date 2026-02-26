"""
core/database.py

Async PostgreSQL connection pool using SQLAlchemy 2.0 + asyncpg.
All database operations in this app are async — never use the
synchronous session in API handlers.

Usage in route handlers:
    async def my_route(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(User).where(User.id == user_id))
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base.
    All ORM models inherit from this.
    """
    pass


# ─── Engine ─────────────────────────────────────────────────────────────────

def _create_engine() -> AsyncEngine:
    """
    Create the async engine with appropriate settings per environment.
    In testing, NullPool prevents connection leaks between test cases.
    """
    kwargs: dict = {
        "echo": settings.debug,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    if settings.environment == "testing":
        kwargs = {"echo": True, "poolclass": NullPool}
    else:
        kwargs.update({
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
        })

    return create_async_engine(settings.async_database_url, **kwargs)


engine: AsyncEngine = _create_engine()

# ─── Session Factory ────────────────────────────────────────────────────────

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ─── Dependencies ────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.
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


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager version for use outside of FastAPI request context.
    Used by background jobs and scheduled tasks.
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


# ─── Lifecycle ───────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Called at application startup.
    Attempts to verify DB connection but does NOT crash the app if it fails.
    This allows the app to start even if the DB is momentarily unreachable.
    """
    from sqlalchemy import text

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection verified successfully.")

            result = await conn.execute(
                text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
            )
            count = result.scalar()
            if count == 0:
                logger.warning(
                    "pgvector extension not found. Vector features will not work. "
                    "Run: CREATE EXTENSION vector; in your PostgreSQL instance."
                )
            else:
                logger.info("pgvector extension confirmed.")

    except Exception as e:
        logger.warning(
            f"Could not connect to database at startup: {e}. "
            "The app will start anyway — DB connections will be retried per request."
        )


async def close_db() -> None:
    """Called at application shutdown to cleanly close the connection pool."""
    await engine.dispose()
    