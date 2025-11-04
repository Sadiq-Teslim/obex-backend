"""Device-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class DeviceBase(BaseModel):
    device_id: str = Field(description="Unique identifier for the device")
    vehicle_make: Optional[str] = Field(default=None, description="Vehicle manufacturer")
    vehicle_model: Optional[str] = Field(default=None, description="Vehicle model")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "device_id": "raspberry-pi-001",
                "vehicle_make": "Toyota",
                "vehicle_model": "Camry"
            }]
        }
    }


class DeviceCreate(DeviceBase):
    """Schema for creating a new device. ID is auto-generated."""
    pass


class DeviceStatusUpdate(BaseModel):
    device_id: str = Field(description="Device identifier")
    status: str = Field(description="Status of the device", pattern="^(online|offline|error)$")
    last_seen: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "device_id": "raspberry-pi-001",
                "status": "online",
                "last_seen": "2025-11-03T21:22:12.708Z"
            }]
        }
    }


class Device(DeviceBase):
    """Schema for device response with auto-generated fields."""
    id: uuid.UUID = Field(..., description="Auto-generated device ID")
    created_at: datetime = Field(..., description="When the device was registered")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "device_id": "raspberry-pi-001",
                "vehicle_make": "Toyota",
                "vehicle_model": "Camry",
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "created_at": "2025-11-03T12:00:00Z"
            }
        }
    }