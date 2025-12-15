"""Database configuration (Clean & Stable)."""

import os
import ssl
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.settings import settings

raw_url = os.getenv("DIRECT_DATABASE_URL") or settings.database_url or "sqlite+aiosqlite:///./obex.db"

# Force session-mode port 5432 when the pooler provides 6543
if ":6543" in raw_url:
    print("DEBUG: Switching to Session Mode (Port 5432)...")
    raw_url = raw_url.replace(":6543", ":5432")

# Ensure correct driver
if "postgres" in raw_url and "+asyncpg" not in raw_url:
    raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://")
    raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://")

if "?" in raw_url:
    raw_url = raw_url.split("?")[0]

print("----------------------------------------------------------------")
print(f"DEBUG: Connection URL: {raw_url.split('@')[-1]}") 
print("----------------------------------------------------------------")

connect_args: Dict[str, Any] = {}

if "asyncpg" in raw_url:
    # A. SSL Fix
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_ctx
    
    # B. Timeout Settings (Valid for asyncpg)
    connect_args["command_timeout"] = 60
    
    # C. Cache Settings (Safety for Supabase)
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    raw_url,
    echo=False,
    future=True,
    connect_args=connect_args,
    # Connection health options to prevent dropped sessions
    pool_pre_ping=True,  # Automatically detects and discards dead connections
    pool_recycle=300,    # Refreshes connections every 5 minutes
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def connect_db() -> None:
    if "sqlite" in raw_url: 
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def close_db() -> None:
    await engine.dispose()