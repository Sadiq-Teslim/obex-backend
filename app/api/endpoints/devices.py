"""Device endpoint handlers."""

from fastapi import APIRouter, HTTPException
from app.models import Device
from app.schemas.devices import DeviceCreate, Device as DeviceSchema
from app.db.session import get_db_session

router = APIRouter(
    prefix="/api/devices",
    tags=["Devices"]
)


@router.post(
    "/register",
    response_model=DeviceSchema,
    summary="Register a new device",
    description="""Register a new edge device (e.g., Raspberry Pi) with the system.
    Returns the created device with auto-generated ID.""",
    status_code=201
)
async def register_device(device: DeviceCreate, db=get_db_session):
    """
    Register a new edge device.
    
    - **device_id**: Unique identifier for the device (e.g., 'raspberry-pi-001')
    - **vehicle_make**: Optional vehicle manufacturer
    - **vehicle_model**: Optional vehicle model
    """
    async with db as session:
        new_device = Device(**device.model_dump())
        session.add(new_device)
        await session.commit()
        await session.refresh(new_device)
        return new_device