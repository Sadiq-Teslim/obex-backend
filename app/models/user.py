"""User model for authentication (signup/login)."""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    # Store only the password hash (Argon2)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False, default="")
    ip_address = Column(String, nullable=True)
    path = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
