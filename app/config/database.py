"""Database configuration for the application."""

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.settings import settings

DEFAULT_DB_URL = "sqlite+aiosqlite:///./obex.db"
DEFAULT_TEST_DB_URL = "sqlite+aiosqlite:///./test.db"


def _normalise_database_url(raw_url: str | None, *, default: str) -> str:
    url_value = raw_url or default
    try:
        url_obj = make_url(url_value)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Invalid DATABASE_URL provided: {url_value}") from exc

    driver = (url_obj.drivername or "").lower()
    if driver.startswith("postgres") and "asyncpg" not in driver:
        url_obj = url_obj.set(drivername="postgresql+asyncpg")
    elif driver in {"sqlite", "sqlite+pysqlite"}:
        url_obj = url_obj.set(drivername="sqlite+aiosqlite")

    return url_obj.render_as_string(hide_password=False)


def normalise_database_url(raw_url: str | None) -> str:
    """Public helper to normalise a database URL for async usage."""
    return _normalise_database_url(raw_url, default=DEFAULT_DB_URL)


def normalise_test_database_url(raw_url: str | None) -> str:
    """Normalise a test database URL, defaulting to the local SQLite test DB."""
    return _normalise_database_url(raw_url, default=DEFAULT_TEST_DB_URL)


DATABASE_URL = normalise_database_url(getattr(settings, "database_url", None))
TEST_DATABASE_URL = normalise_test_database_url(getattr(settings, "test_database_url", None))

# Async SQLAlchemy engine and session factory used across the application
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base for ORM models
Base = declarative_base()


async def connect_db() -> None:
    """Initialise database schema if it does not yet exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the engine and close all underlying connections."""
    await engine.dispose()