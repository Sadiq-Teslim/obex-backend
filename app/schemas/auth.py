"""Pydantic schemas for signup and login endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic import validator


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


class UserOut(BaseModel):
    id: int
    username: str
    ipAddress: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
