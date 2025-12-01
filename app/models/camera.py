from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.config.database import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    
    camera_name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=True) # Can be empty
    port = Column(Integer, default=554)
    path = Column(String, nullable=False)
    
    rtsp_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)