"""Utility script to initialise the test database schema."""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.config.database import Base, normalise_test_database_url
from app.core.settings import settings


async def create_test_schema() -> None:
    """Create all database tables defined in ORM models for the test DB."""
    database_url = normalise_test_database_url(settings.test_database_url)
    engine = create_async_engine(database_url, echo=True, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_schema())