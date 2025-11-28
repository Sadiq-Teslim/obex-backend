"""Auth endpoints: signup and login."""
from fastapi import APIRouter, HTTPException, Request
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED

from app.schemas.auth import SignupRequest, LoginRequest, UserOut
from app.services.auth_service import create_user, authenticate
from app.services.jwt_service import create_access_token, create_refresh_token, decode_token
from app.services.redis_client import get_redis
from datetime import datetime
from app.core.settings import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/refresh")
async def refresh_token_endpoint(payload: dict):
    """Exchange refresh token for a new access token."""
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    decoded = decode_token(token)
    if not decoded or decoded.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    jti = decoded.get("jti")
    redis = await get_redis()
    stored = await redis.get(f"refresh:{jti}")
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
    # create new access token
    access_token = create_access_token(subject=decoded.get("sub"))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/revoke")
async def revoke_refresh(payload: dict):
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    decoded = decode_token(token)
    if not decoded:
        raise HTTPException(status_code=400, detail="Invalid token")
    jti = decoded.get("jti")
    redis = await get_redis()
    # delete key to revoke
    await redis.delete(f"refresh:{jti}")
    return {"revoked": True}


@router.post("/signup", response_model=UserOut, status_code=HTTP_201_CREATED)
async def signup(payload: SignupRequest):
    try:
        user = await create_user(
            username=payload.username,
            password=payload.password,
            ip_address=payload.ipAddress,
            path=payload.path,
            port=payload.port,
        )
        try:
            return UserOut.from_orm(user)
        except Exception:
            # Fallback: build dict manually to avoid Pydantic ORM incompatibilities
            return UserOut(
                id=getattr(user, "id", None),
                username=getattr(user, "username", None),
                ip_address=getattr(user, "ip_address", None),
                path=getattr(user, "path", None),
                port=getattr(user, "port", None),
                created_at=getattr(user, "created_at", None),
            )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.post("/login")
async def login(request: Request, payload: LoginRequest):
    client_ip = request.client.host if request.client else None
    user = await authenticate(payload.username, payload.password, ip_address=client_ip)
    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials or account locked")

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    # store refresh token jti in redis to allow revocation if needed
    rt_payload = decode_token(refresh_token)
    # Redis operations should not break login. Wrap in try/except so we still
    # return tokens even if Redis is unavailable.
    if rt_payload and rt_payload.get("jti"):
        try:
            redis = await get_redis()
            jti = rt_payload["jti"]
            exp = rt_payload.get("exp")
            # set key with TTL (fallback to JWT expiry minutes if missing)
            if exp is None:
                ttl = int(settings.jwt_exp_minutes * 60)
            else:
                ttl = max(0, int(int(exp) - int(datetime.utcnow().timestamp())))
            await redis.set(f"refresh:{jti}", str(user.id), ex=ttl)
        except Exception:
            # ignore Redis failures for now
            pass

    # Return user info; prefer from_orm but fallback to manual construction.
    try:
        user_out = UserOut.from_orm(user)
    except Exception:
        user_out = UserOut(
            id=getattr(user, "id", None),
            username=getattr(user, "username", None),
            ip_address=getattr(user, "ip_address", None),
            path=getattr(user, "path", None),
            port=getattr(user, "port", None),
            created_at=getattr(user, "created_at", None),
        )

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token, "user": user_out}
