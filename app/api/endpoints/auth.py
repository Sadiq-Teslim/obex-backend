"""Auth endpoints: signup and login."""
from fastapi import APIRouter, HTTPException, Request
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED

from app.schemas.auth import SignupRequest, LoginRequest, UserOut
from app.services.auth_service import create_user, authenticate
from app.services.jwt_service import create_access_token

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
async def login(request: Request, payload: LoginRequest):
    client_ip = request.client.host if request.client else None
    user = await authenticate(payload.username, payload.password, ip_address=client_ip)
    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials or account locked")

    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer", "user": UserOut.from_orm(user)}
