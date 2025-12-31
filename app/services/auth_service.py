"""Authentication service (Refactored for Email Login)."""
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
    email: str,
    phone_number: str,
    password: str
) -> User:
    """Create a new user. Raises ValueError if email exists."""
    password_hash = argon2.hash(password)
    password_salt = secrets.token_hex(16)

    async with AsyncSessionLocal() as session:
        q = select(User).where(User.email == email)
        result = await session.execute(q)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError("Email already registered")

        user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            password_hash=password_hash,
            password_salt=password_salt,
            created_at=datetime.utcnow(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def authenticate(email: str, password: str) -> Optional[User]:
    """Authenticate by EMAIL."""
    async with AsyncSessionLocal() as session:
        q = select(User).where(User.email == email)
        result = await session.execute(q)
        user = result.scalar_one_or_none()

        if not user:
            return None

        now = datetime.utcnow()
        locked_until = getattr(user, "locked_until", None)
        if locked_until is not None and locked_until > now:
            return None

        try:
            verified = argon2.verify(password, user.password_hash)
        except Exception:
            verified = False

        if verified:
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(failed_attempts=0, locked_until=None, last_login_at=now)
            )
            await session.commit()
            return user

        failed_val = getattr(user, "failed_attempts", None)
        try:
            failed_int = int(failed_val or 0)
        except (TypeError, ValueError):
            failed_int = 0
        new_failed = failed_int + 1
        locked_until = None
        if new_failed >= MAX_FAILED_ATTEMPTS:
            locked_until = now + timedelta(minutes=LOCK_MINUTES)

        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(failed_attempts=new_failed, locked_until=locked_until)
        )
        await session.commit()
        return None
    
async def get_user_by_id(user_id: int) -> Optional[User]:
    """Retrieve a user by their ID."""
    async with AsyncSessionLocal() as session:
        q = select(User).where(User.id == user_id)
        result = await session.execute(q)
        user = result.scalar_one_or_none()
        return user