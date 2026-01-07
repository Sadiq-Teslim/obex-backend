import uuid
from sqlalchemy import Column, Integer, String, DateTime
from app.config.database import Base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False, default="")

    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime)