from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas.camera import CameraCreate, CameraResponse
from app.models.camera import Camera
from app.config.database import AsyncSessionLocal

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

@router.post("/create", response_model=CameraResponse)
async def create_camera(payload: CameraCreate):
    """Create a camera entry and persist its RTSP endpoint."""
    rtsp_url = f"rtsp://{payload.username}:{payload.password}@{payload.ipAddress}:{payload.port}/{payload.path}"
    
    async with AsyncSessionLocal() as session:
        new_camera = Camera(
            camera_name=payload.cameraName,
            ip_address=payload.ipAddress,
            username=payload.username,
            password=payload.password,
            port=payload.port,
            path=payload.path,
            rtsp_url=rtsp_url,
            created_at=datetime.utcnow()
        )
        
        session.add(new_camera)
        try:
            await session.commit()
            await session.refresh(new_camera)
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
            
    return {
        "message": "Camera created successfully",
        "data": {
            "cameraName": new_camera.camera_name,
            "rtspUrl": new_camera.rtsp_url
        }
    }