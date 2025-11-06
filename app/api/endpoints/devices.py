"""Device endpoint handlers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import Device
from app.schemas.devices import DeviceCreate, Device as DeviceSchema

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
async def register_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a new edge device.
    
    - **device_id**: Unique identifier for the device (e.g., 'raspberry-pi-001')
    - **vehicle_make**: Optional vehicle manufacturer
    - **vehicle_model**: Optional vehicle model
    """
    new_device = Device(**device.model_dump())
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    return new_device