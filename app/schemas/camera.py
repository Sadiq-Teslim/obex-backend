import uuid
from pydantic import BaseModel

class CameraCreate(BaseModel):
    cameraName: str
    ipAddress: str
    username: str
    password: str = "" # Default to empty string if missing
    port: int = 554
    path: str

class CameraData(BaseModel):
    id: uuid.UUID
    cameraName: str
    rtspUrl: str
    user_id: uuid.UUID

class CameraResponse(BaseModel):
    message: str
    data: CameraData