"""Device models for the database."""

from sqlalchemy import Column, String, DateTime
import uuid
from datetime import datetime

from app.db.base import Base


class Device(Base):
    """
    Database model for registered edge devices.
    Stores device identification and associated vehicle information.
    """
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, unique=True, nullable=False)
    vehicle_make = Column(String)
    vehicle_model = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)