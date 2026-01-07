import uuid
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.config.database import Base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(PG_UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True))
    
    camera_name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=True)
    port = Column(Integer, default=554)
    path = Column(String, nullable=False)
    
    rtsp_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)