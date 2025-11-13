"""Alert models for the database."""

from sqlalchemy import Column, String, Float, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID
import json
import uuid

from app.db.base import Base


class Alert(Base):
    """
    Database model for security alerts.
    Stores alert details including location, type, and additional payload data.
    """
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    alert_type = Column(String, nullable=False)
    location_lat = Column(Float)
    location_lon = Column(Float)
    payload = Column(JSON)
    
    def __init__(self, **kwargs):
        # Ensure payload is a string if it's a dict
        if 'payload' in kwargs and isinstance(kwargs['payload'], dict):
            kwargs['payload'] = json.dumps(kwargs['payload'])
        super().__init__(**kwargs)