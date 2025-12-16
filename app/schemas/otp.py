from pydantic import BaseModel, EmailStr

class OTPGenerateRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class OTPResponse(BaseModel):
    message: str