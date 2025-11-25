"""User model for authentication (signup/login)."""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_salt = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    path = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
