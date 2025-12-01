from pydantic import BaseModel

class CameraCreate(BaseModel):
    cameraName: str
    ipAddress: str
    username: str
    password: str = "" # Default to empty string if missing
    port: int = 554
    path: str

class CameraData(BaseModel):
    cameraName: str
    rtspUrl: str

class CameraResponse(BaseModel):
    message: str
    data: CameraData