from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

# --- Device Schemas ---

class DeviceBase(BaseModel):
    device_id: str
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceStatusUpdate(BaseModel):
    device_id: str
    status: Literal['online', 'offline', 'error']
    last_seen: datetime

class Device(DeviceBase):
    id: int # Internal DB ID
    created_at: datetime
    
    class Config:
        orm_mode = True

# --- Alert Schemas ---
# [cite_start]Based on the modules from the Engagement Proposal [cite: 9, 10, 11, 12, 13, 14, 15, 16]

class AlertBase(BaseModel):
    device_id: str
    timestamp: datetime
    alert_type: Literal[
        'weapon_detection',
        'unauthorized_passenger',
        'aggression_detection',
        'harassment_detection',
        'robbery_pattern',
        'route_deviation',
        'driver_fatigue',
        'distress_detection'
    ]
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    payload: Optional[dict] = None # For extra data, e.g., bounding box

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int # Internal DB ID

    class Config:
        orm_mode = True