from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    phoneNumber: str
    password: str
    confirmPassword: str

    @validator('confirmPassword')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str