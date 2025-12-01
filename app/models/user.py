from sqlalchemy import Column, Integer, String, DateTime
from app.config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # New Requirements
    username = Column(String, nullable=False) # Name only, not for login
    email = Column(String, unique=True, index=True, nullable=False) # Login ID
    phone_number = Column(String, nullable=True)
    
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False, default="")

    # Security fields
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime)