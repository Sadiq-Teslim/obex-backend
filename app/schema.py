from pydantic import BaseModel, field_validator, Field
from pydantic.json_schema import JsonSchemaValue
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import uuid

# --- Device Schemas ---
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
    status: Literal['online', 'offline', 'error']
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
        "from_attributes": True,  # Pydantic v2: allows .from_orm() to work
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

# --- Alert Schemas ---
class AlertBase(BaseModel):
    device_id: str = Field(description="ID of the device that detected the alert")
    timestamp: datetime = Field(description="When the alert occurred")
    alert_type: Literal[
        'weapon_detection',
        'unauthorized_passenger',
        'aggression_detection',
        'harassment_detection',
        'robbery_pattern',
        'route_deviation',
        'driver_fatigue',
        'distress_detection'
    ] = Field(description="Type of security event")
    location_lat: Optional[float] = Field(default=None, description="Latitude coordinate")
    location_lon: Optional[float] = Field(default=None, description="Longitude coordinate")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Additional data like confidence score or bounding box")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "device_id": "raspberry-pi-001",
                "timestamp": "2025-11-03T21:22:12.708Z",
                "alert_type": "weapon_detection",
                "location_lat": 6.5244,
                "location_lon": 3.3792,
                "payload": {
                    "confidence": 0.95,
                    "camera": "front"
                }
            }]
        }
    }

class AlertCreate(AlertBase):
    """Schema for creating a new alert. ID is auto-generated. DO NOT include 'id' field in your request."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "raspberry-pi-001",
                "timestamp": "2025-11-03T21:22:12.708Z",
                "alert_type": "weapon_detection",
                "location_lat": 6.5244,
                "location_lon": 3.3792,
                "payload": {
                    "confidence": 0.95,
                    "camera": "front"
                }
            }
        }
    }

class Alert(AlertBase):
    """Schema for alert response with auto-generated ID."""
    id: uuid.UUID = Field(..., description="Auto-generated alert ID")

    model_config = {
        "from_attributes": True,  # Pydantic v2: allows .from_orm() to work
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "device_id": "raspberry-pi-001",
                "timestamp": "2025-11-03T21:22:12.708Z",
                "alert_type": "weapon_detection",
                "location_lat": 6.5244,
                "location_lon": 3.3792,
                "payload": {
                    "confidence": 0.95,
                    "camera": "front"
                }
            }
        }
    }

    @field_validator("payload", mode="before")
    def parse_payload(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v