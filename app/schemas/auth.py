"""Pydantic schemas for signup and login endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SignupRequest(BaseModel):
    username: str
    password: str
    ipAddress: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None


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
