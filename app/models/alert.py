"""Alert models for the database."""

from sqlalchemy import Column, String, Float, TIMESTAMP
import os
from sqlalchemy.dialects.postgresql import UUID, JSON
import json
import uuid

from app.db.base import Base


class Alert(Base):
    """
    Database model for security alerts.
    Stores alert details including location, type, and additional payload data.
    """
    __tablename__ = "alerts"
    
    # Use String for SQLite, UUID for PostgreSQL
    import os
    from sqlalchemy import String as SQLString
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    db_dialect = os.environ.get("TEST_DB_DIALECT", "sqlite")
    if db_dialect == "sqlite":
        id = Column(SQLString, primary_key=True, default=lambda: str(uuid.uuid4()))
    else:
        id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
        # Ensure id is a string for SQLite
        db_dialect = os.environ.get("TEST_DB_DIALECT", "sqlite")
        if db_dialect == "sqlite" and 'id' in kwargs and not isinstance(kwargs['id'], str):
            kwargs['id'] = str(kwargs['id'])
        super().__init__(**kwargs)