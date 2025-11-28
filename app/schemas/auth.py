"""Pydantic schemas for signup and login endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic import validator

# Detect Pydantic v2 vs v1. In v2, BaseModel has `model_config` attribute; in v1
# we should use `Config.orm_mode = True`. Create classes conditionally to avoid
# mixing `model_config` and `Config` which raises an error in v2.
_IS_PYDANTIC_V2 = hasattr(BaseModel, "model_config")


class SignupRequest(BaseModel):
    username: str
    password: str
    ipAddress: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None
    @validator("password")
    def password_complexity(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        if not any(c.isdigit() for c in v):
            raise ValueError("password must include a number")
        if not any(c.isalpha() for c in v):
            raise ValueError("password must include a letter")
        return v



class LoginRequest(BaseModel):
    username: str
    password: str


if _IS_PYDANTIC_V2:
    class UserOut(BaseModel):
        id: int
        username: str
        ip_address: Optional[str] = None
        path: Optional[str] = None
        port: Optional[int] = None
        created_at: datetime

        model_config = {"from_attributes": True}
else:
    class UserOut(BaseModel):
        id: int
        username: str
        ip_address: Optional[str] = None
        path: Optional[str] = None
        port: Optional[int] = None
        created_at: datetime

        class Config:
            orm_mode = True
