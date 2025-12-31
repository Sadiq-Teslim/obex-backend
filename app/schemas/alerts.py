"""Alert-related Pydantic schemas."""

from pydantic import BaseModel, field_validator, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import uuid


class AlertBase(BaseModel):
    device_id: str = Field(description="ID of the device that detected the alert")
    user_id: str = Field(default=None, description="ID of the user associated with the device")
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
    """Schema for creating a new alert. ID is auto-generated."""
    pass


class Alert(AlertBase):
    """Schema for alert response with auto-generated ID."""
    id: uuid.UUID = Field(..., description="Auto-generated alert ID")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f6heu2y7",
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