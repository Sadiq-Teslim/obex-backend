"""Database session configuration and utilities."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import AsyncSessionLocal

__all__ = ["AsyncSessionLocal", "get_db_session"]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        yield session