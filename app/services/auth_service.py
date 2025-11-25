"""Authentication service: password hashing and user CRUD for signup/login."""
import os
import hashlib
import binascii
from typing import Optional
from datetime import datetime

from sqlalchemy import select

from app.models.user import User
from app.db.session import AsyncSessionLocal


def _hash_password(password: str, salt: bytes) -> str:
    """Hash a password with provided salt using PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(dk).decode("ascii")


async def create_user(username: str, password: str, ip_address: Optional[str] = None, path: Optional[str] = None, port: Optional[int] = None) -> User:
    """Create a new user. Raises ValueError if username exists."""
    async with AsyncSessionLocal() as session:
        # check existing
        q = select(User).where(User.username == username)
        result = await session.execute(q)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("username already exists")

        salt = os.urandom(16)
        password_hash = _hash_password(password, salt)
        user = User(
            username=username,
            password_salt=binascii.hexlify(salt).decode("ascii"),
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


async def authenticate(username: str, password: str) -> Optional[User]:
    """Return user if authentication succeeds, otherwise None."""
    async with AsyncSessionLocal() as session:
        q = select(User).where(User.username == username)
        result = await session.execute(q)
        user = result.scalar_one_or_none()
        if not user:
            return None
        salt = binascii.unhexlify(user.password_salt.encode("ascii"))
        candidate_hash = _hash_password(password, salt)
        if hashlib.compare_digest(candidate_hash, user.password_hash):
            return user
        return None
