from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import UserSignup, UserLogin, Token
from app.services import auth_service, jwt_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignup):
    try:
        user = await auth_service.create_user(
            username=payload.username,
            email=payload.email,
            phone_number=payload.phoneNumber,
            password=payload.password
        )
        return {"message": "User created successfully", "userId": user.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.post("/login", response_model=Token)
async def login(payload: UserLogin):
    user = await auth_service.authenticate(
        email=payload.email, 
        password=payload.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    access_token = jwt_service.create_access_token(subject=str(user.email))
    return {"access_token": access_token, "token_type": "bearer"}