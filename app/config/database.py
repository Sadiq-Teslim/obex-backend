"""Database configuration (Clean & Stable)."""

import os
import ssl
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.settings import settings

# --- 1. SETUP URL ---
raw_url = os.getenv("DIRECT_DATABASE_URL") or settings.database_url or "sqlite+aiosqlite:///./obex.db"

# Force Port 5432 (Session Mode) - This is the port that works for you
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

# --- 2. CONFIGURE CONNECTION ---
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

# --- 3. CREATE ENGINE ---
engine = create_async_engine(
    raw_url,
    echo=False,
    future=True,
    connect_args=connect_args,
    # THE REAL FIX FOR DROPPED CONNECTIONS:
    pool_pre_ping=True,  # Automatically detects and discards dead connections
    pool_recycle=300,    # Refreshes connections every 5 minutes
    pool_size=10,
    max_overflow=20,
)

# --- 4. SESSION FACTORY ---
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