from pydantic import BaseModel,EmailStr,Field,field_validator
from typing import Optional,List,Literal

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(
        min_length=8,  # too short = rejected
        max_length=72  # too long = rejected before reaching bcrypt
    )

# Schema to update user profile details
# ─────────────────────────────────────────────────────────────
# Strict literal types (enums) for data quality
# ─────────────────────────────────────────────────────────────
Gender = Literal["male","female","other"]
SocialSupportLevel = Literal["high","medium","low"]
OccupationType = Literal["student", "working", "unemployed", "retired", "other"]

class UserProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=10, le=100, description="Age must be between 18 and 100")
    gender: Optional[Gender] = Field(None, description="User's gender")
    occupation: Optional[OccupationType] = Field(None, description="Current occupation")
    sleep_hours: Optional[int] = Field(None, ge=0, le=24, description="Average sleep hours per night (0-24)")
    social_support: Optional[SocialSupportLevel] = Field(None, description="Perceived social support level")
    life_events: Optional[List[str]] = Field(default_factory=list, description="Recent significant life events (max 5, non-empty)")
    @field_validator('life_events')
    @classmethod
    def validate_life_events(cls, v:List[str]) -> List[str]:
        clean_life_events = [event.strip() for event in v if event.strip()]
        return clean_life_events[:5]

# ─────────────────────────────────────────────────────────────
# Phase 2 User Profile response
# ─────────────────────────────────────────────────────────────
class UserProfileResponse(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    sleep_hours: Optional[int] = None
    social_support: Optional[str] = None
    life_events: Optional[List[str]] = None

# Schema for user login request
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Schema to deside the structure of user response
class UserResponse(BaseModel):
    email:EmailStr

# Schema to deside the structure of Token response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"   # ← default value

# Schema to deside the structure of Refresh Token response
class RefreshRequest(BaseModel):
    refresh_token: str