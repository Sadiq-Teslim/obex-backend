"""Authentication service: Argon2 password hashing, lockout and user CRUD.

This module uses the properly configured SQLAlchemy session from app.config.database.
The legacy fallback logic has been removed to prevent error masking and logic bugs.
"""
import logging
import secrets
from typing import Optional
from datetime import datetime, timedelta

from passlib.hash import argon2
from sqlalchemy import select, update

from app.models.user import User
from app.config.database import AsyncSessionLocal

LOG = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15


async def create_user(
    username: str, 
    password: str, 
    ip_address: Optional[str] = None, 
    path: Optional[str] = None, 
    port: Optional[int] = None
) -> User:
    """Create a new user. Raises ValueError if username exists."""
    password_hash = argon2.hash(password)
    password_salt = secrets.token_hex(16)

    async with AsyncSessionLocal() as session:
        # 1. Check if user exists
        # We do this inside the transaction to ensure consistency
        q = select(User).where(User.username == username)
        result = await session.execute(q)
        existing = result.scalar_one_or_none()
        
        if existing:
            # We raise this BEFORE the try/except block could catch it erroneously
            raise ValueError("Username already exists")

        # 2. Create new user
        user = User(
            username=username,
            password_hash=password_hash,
            password_salt=password_salt,
            ip_address=ip_address,
            path=path,
            port=port,
            created_at=datetime.utcnow(),
        )
        session.add(user)
        
        try:
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as exc:
            await session.rollback()
            LOG.error(f"Error creating user {username}: {exc}")
            raise exc


async def authenticate(username: str, password: str, ip_address: Optional[str] = None) -> Optional[User]:
    """Return user on successful authentication, otherwise None. Handles lockout."""
    async with AsyncSessionLocal() as session:
        q = select(User).where(User.username == username)
        result = await session.execute(q)
        user = result.scalar_one_or_none()

        if not user:
            return None

        now = datetime.utcnow()
        
        # Check lockout
        locked_until_val = getattr(user, "locked_until", None)
        if isinstance(locked_until_val, datetime) and locked_until_val > now:
            LOG.warning(f"User {username} is locked out until {locked_until_val}")
            return None

        # Verify password
        try:
            verified = argon2.verify(password, user.password_hash)
        except Exception:
            verified = False

        if verified:
            # Success: Reset counters
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    failed_attempts=0, 
                    locked_until=None, 
                    last_login_at=now, 
                    last_login_ip=ip_address
                )
            )
            await session.commit()
            await session.refresh(user)
            return user

        # Failure: Update Lockout logic
        # Ensure we operate on plain Python ints to avoid SQLAlchemy ColumnElement in comparisons
        failed_attempts_val = getattr(user, "failed_attempts", 0) or 0
        try:
            new_failed = int(failed_attempts_val) + 1
        except (TypeError, ValueError):
            new_failed = 1
        locked_until = None
        
        if new_failed >= MAX_FAILED_ATTEMPTS:
            locked_until = now + timedelta(minutes=LOCK_MINUTES)
            LOG.warning(f"User {username} locked out due to too many failed attempts.")

        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(failed_attempts=new_failed, locked_until=locked_until)
        )
        await session.commit()
        
        return None