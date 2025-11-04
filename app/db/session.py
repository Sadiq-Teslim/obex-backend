"""Database session configuration and utilities."""

from app.config.database import AsyncSessionLocal, engine


async def get_db_session():
    """Dependency for getting a database session."""
    async with AsyncSessionLocal() as session:
        yield session