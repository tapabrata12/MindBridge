from pydantic import BaseModel,EmailStr,Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,  # too short = rejected
        max_length=72  # too long = rejected before reaching bcrypt
    )

# Schema for user login request
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email:EmailStr

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"   # ← default value

class RefreshRequest(BaseModel):
    refresh_token: str