"""JWT helper service for creating and verifying access tokens."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt

from app.core.settings import settings


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    secret = settings.jwt_secret
    algorithm = settings.jwt_algorithm
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_exp_minutes))
    payload: Dict[str, Any] = {"sub": subject, "exp": expire, "iat": datetime.utcnow()}
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except Exception:
        return None
