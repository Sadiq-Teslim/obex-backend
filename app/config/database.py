"""Database configuration for the application.

This module provides a minimal, import-safe set of objects for other
modules to consume without causing circular imports.

Exports:
  - engine: SQLAlchemy async engine
  - AsyncSessionLocal: session factory
  - Base: declarative base for models
  - connect_db(): coroutine to create tables
  - close_db(): coroutine to dispose engine
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Using an environment variable for the DB URL, fallback to a local sqlite async DB for testing.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Create the async engine and session factory (callable)
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Base for models
Base = declarative_base()


async def connect_db():
    """Create tables (runs Base.metadata.create_all) in an async context."""
    async with engine.begin() as conn:
        print("Creating database tables (connect_db)...")
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created (connect_db).")


async def close_db():
    """Gracefully dispose the engine."""
    await engine.dispose()
    print("Database engine disposed (close_db).")