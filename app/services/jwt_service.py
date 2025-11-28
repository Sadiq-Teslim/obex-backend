"""JWT helper service for creating and verifying access tokens."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt

from app.core.settings import settings
from uuid import uuid4


def _now_ts() -> int:
    return int(datetime.utcnow().timestamp())


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    secret = settings.jwt_secret
    algorithm = settings.jwt_algorithm
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_exp_minutes))
    jti = str(uuid4())
    payload: Dict[str, Any] = {"sub": subject, "exp": expire, "iat": datetime.utcnow(), "jti": jti}
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    # refresh tokens longer lived (e.g., 7 days)
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    jti = str(uuid4())
    payload: Dict[str, Any] = {"sub": subject, "exp": expire, "iat": datetime.utcnow(), "jti": jti, "typ": "refresh"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except Exception:
        return None
