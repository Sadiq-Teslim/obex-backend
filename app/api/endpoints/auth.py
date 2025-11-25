"""Auth endpoints: signup and login."""
from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED

from app.schemas.auth import SignupRequest, LoginRequest, UserOut
from app.services.auth_service import create_user, authenticate

router = APIRouter(prefix="/api/auth", tags=["Auth"])


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
        return UserOut.from_orm(user)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.post("/login")
async def login(payload: LoginRequest):
    user = await authenticate(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # For now return basic user info; token generation can be added later
    return {"success": True, "user": UserOut.from_orm(user)}
