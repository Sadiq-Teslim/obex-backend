"""Authentication service: Argon2 password hashing, lockout and user CRUD."""
from typing import Optional
from datetime import datetime, timedelta

from passlib.hash import argon2
from sqlalchemy import select, update

from app.models.user import User
from app.db.session import AsyncSessionLocal


MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15


async def create_user(username: str, password: str, ip_address: Optional[str] = None, path: Optional[str] = None, port: Optional[int] = None) -> User:
    """Create a new user. Raises ValueError if username exists."""
    async with AsyncSessionLocal() as session:
        q = select(User).where(User.username == username)
        result = await session.execute(q)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("username already exists")

        password_hash = argon2.hash(password)
        user = User(
            username=username,
            password_hash=password_hash,
            ip_address=ip_address,
            path=path,
            port=port,
            created_at=datetime.utcnow(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def authenticate(username: str, password: str, ip_address: Optional[str] = None) -> Optional[User]:
    """Return user on successful authentication, otherwise None. Handles lockout and failed attempts."""
    async with AsyncSessionLocal() as session:
        q = select(User).where(User.username == username)
        result = await session.execute(q)
        user = result.scalar_one_or_none()
        if not user:
            return None

        now = datetime.utcnow()
        if user.locked_until and user.locked_until > now:
            # account locked
            return None

        # verify password
        try:
            verified = argon2.verify(password, user.password_hash)
        except Exception:
            verified = False

        if verified:
            # reset failed attempts and update last login
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(failed_attempts=0, locked_until=None, last_login_at=now, last_login_ip=ip_address)
            )
            await session.commit()
            # refresh user
            await session.refresh(user)
            return user

        # failed attempt
        new_failed = user.failed_attempts + 1
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
