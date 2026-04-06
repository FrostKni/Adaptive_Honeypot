"""
Database connection and session management.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager

from src.core.config import settings


# SQLite does not support pool_size/max_overflow/pool_recycle — use NullPool
_is_sqlite = settings.db.async_url.startswith("sqlite")
engine = create_async_engine(
    settings.db.async_url,
    echo=settings.db.echo,
    **({"poolclass": NullPool} if _is_sqlite else {
        "pool_size": settings.db.pool_size,
        "max_overflow": settings.db.max_overflow,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """Context manager for database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    from src.core.db.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()