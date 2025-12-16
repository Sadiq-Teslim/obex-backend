from fastapi import APIRouter, HTTPException, status
from app.schemas.otp import OTPGenerateRequest, OTPVerifyRequest, OTPResponse
from app.services import otp_service

router = APIRouter(prefix="/api/otp", tags=["OTP"])

@router.post("/generate", response_model=OTPResponse)
async def generate_otp_endpoint(payload: OTPGenerateRequest):
    """Generates an OTP and sends it via email."""
    try:
        await otp_service.generate_otp(payload.email)
        return {"message": "OTP sent successfully to your email"}
    except Exception as e:
        print(f"Error sending OTP: {e}") 
        raise HTTPException(status_code=500, detail="Failed to send OTP. Please check email configuration.")

@router.post("/verify", response_model=OTPResponse)
async def verify_otp_endpoint(payload: OTPVerifyRequest):
    """Verifies the provided OTP."""
    is_valid = await otp_service.verify_otp(payload.email, payload.otp)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid or expired OTP"
        )
    
    return {"message": "OTP verified successfully"}