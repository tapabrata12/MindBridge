# File: server/src/schemas/user.py  # Full file path comment as requested

from typing import List, Literal, Optional  # Import typing helpers for optional values and strict literal enums
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator  # Import Pydantic v2 tools for schema validation


Gender = Literal["male", "female", "other"]  # Define strict allowed gender values
SocialSupportLevel = Literal["high", "medium", "low"]  # Define strict allowed social support values
OccupationType = Literal["student", "working", "unemployed", "retired", "other"]  # Define strict allowed occupation values


class UserCreate(BaseModel):  # Define request schema for user registration
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)  # Forbid unknown fields and auto-strip strings
    email: EmailStr = Field(..., description="User email address")  # Require a valid email format
    password: str = Field(..., min_length=8, max_length=72, description="Password length must be 8-72 characters for bcrypt compatibility")  # Enforce safe bcrypt-compatible password range


class UserLogin(BaseModel):  # Define request schema for user login
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)  # Forbid unknown fields and trim string whitespace
    email: EmailStr = Field(..., description="Registered email address")  # Require valid email for login
    password: str = Field(..., min_length=8, max_length=72, description="Password length must be 8-72 characters")  # Keep consistent password constraints across auth flows


class RefreshRequest(BaseModel):  # Define request schema for refresh token exchange
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)  # Forbid unknown fields and normalize whitespace
    refresh_token: str = Field(..., min_length=20, description="Valid JWT refresh token")  # Require non-trivial token length input


class TokenResponse(BaseModel):  # Define standardized token payload schema
    model_config = ConfigDict(extra="forbid")  # Forbid extra response fields for contract consistency
    access_token: str = Field(..., description="Short-lived JWT access token")  # Include access token used for protected API calls
    refresh_token: str = Field(..., description="Long-lived JWT refresh token used for token rotation")  # Include refresh token used to mint new access tokens
    token_type: str = Field(default="bearer", description="OAuth2 token type")  # Default token type remains bearer for compatibility


class UserResponse(BaseModel):  # Define minimal safe authenticated user response
    model_config = ConfigDict(extra="forbid")  # Forbid unknown fields for strict outbound schema
    email: EmailStr = Field(..., description="Authenticated user's email")  # Return only the user email in /me response


class UserProfileUpdate(BaseModel):  # Define request schema for partial profile updates
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)  # Reject unknown fields and normalize strings
    age: Optional[int] = Field(default=None, ge=10, le=100, description="User age between 10 and 100")  # Validate reasonable age range
    gender: Optional[Gender] = Field(default=None, description="User gender")  # Restrict gender values to known literals
    occupation: Optional[OccupationType] = Field(default=None, description="Current occupation")  # Restrict occupation values to known literals
    sleep_hours: Optional[int] = Field(default=None, ge=0, le=24, description="Average sleep hours per night (0-24)")  # Enforce realistic sleep-hour boundaries
    social_support: Optional[SocialSupportLevel] = Field(default=None, description="Perceived social support level")  # Restrict support values to known literals
    life_events: Optional[List[str]] = Field(default_factory=list, description="Recent significant life events (max 5 items)")  # Store up to 5 cleaned life-event strings

    @field_validator("life_events")  # Attach validator to life_events field
    @classmethod  # Mark validator as class-level method per Pydantic v2 style
    def validate_life_events(cls, value: Optional[List[str]]) -> List[str]:  # Validate and normalize life events list
        if value is None:  # Handle omitted/null values safely
            return []  # Return empty list default for consistent downstream handling
        cleaned_events = [event.strip() for event in value if isinstance(event, str) and event.strip()]  # Trim whitespace and remove empty/non-string entries
        return cleaned_events[:5]  # Cap list size to maximum 5 items


class UserProfileResponse(BaseModel):  # Define response schema for user profile reads/writes
    model_config = ConfigDict(extra="forbid")  # Forbid unknown output fields for stable API contract
    age: Optional[int] = Field(default=None, description="User age")  # Return age if present
    gender: Optional[Gender] = Field(default=None, description="User gender")  # Return gender using strict enum typing
    occupation: Optional[OccupationType] = Field(default=None, description="User occupation")  # Return occupation using strict enum typing
    sleep_hours: Optional[int] = Field(default=None, ge=0, le=24, description="Average sleep hours per night")  # Return bounded sleep hours
    social_support: Optional[SocialSupportLevel] = Field(default=None, description="Perceived social support level")  # Return support level using strict enum typing
    life_events: Optional[List[str]] = Field(default_factory=list, description="Recent significant life events")  # Return cleaned life-events list