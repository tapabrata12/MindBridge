# File: server/src/api/routes/profile.py  # Full file path comment as requested

from typing import Any, Dict  # Import typing helpers for dependency-injected user data
from fastapi import APIRouter, Depends, HTTPException, status  # Import FastAPI router and HTTP error/status helpers
from src.core.config import settings  # Import app settings for API prefix
from src.core.dependencies import search_user  # Import JWT auth dependency for protected profile routes
from src.schemas.user import UserProfileResponse, UserProfileUpdate  # Import Pydantic v2 profile schemas
from src.services.user_service import get_user_profile, user_profile_update  # Import profile business logic functions

router = APIRouter(prefix=f"{settings.PREFIX}/profile", tags=["Profile"])  # Create profile router at /api/profile


@router.get("", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)  # Define GET /api/profile endpoint
async def get_profile(user: Dict[str, Any] = Depends(search_user)) -> UserProfileResponse:  # Read current authenticated user's profile
    user_id = user.get("_id")  # Extract user ID resolved by auth dependency
    if not isinstance(user_id, str) or not user_id.strip():  # Validate user ID shape before calling service
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")  # Return 401 for broken auth context

    try:  # Start controlled service call block
        profile = await get_user_profile(user_id)  # Fetch profile from service by authenticated user ID
        return profile  # Return validated profile response
    except HTTPException:  # Re-raise known service HTTP errors unchanged
        raise  # Preserve original status and detail from service layer
    except Exception as exc:  # Catch unexpected runtime/database exceptions
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch profile: {str(exc)}")  # Return safe 500 response


@router.put("", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)  # Define PUT /api/profile endpoint
async def update_profile(profile_update: UserProfileUpdate, user: Dict[str, Any] = Depends(search_user)) -> UserProfileResponse:  # Update current authenticated user's profile
    user_id = user.get("_id")  # Extract authenticated user ID from dependency result
    if not isinstance(user_id, str) or not user_id.strip():  # Validate user ID before service operation
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")  # Return 401 when auth context is malformed

    try:  # Start controlled update operation block
        updated_profile = await user_profile_update(user_id, profile_update)  # Apply profile update via service layer
        return updated_profile  # Return updated profile response model
    except HTTPException:  # Re-raise expected service-level HTTP exceptions
        raise  # Keep service-provided status code and message
    except Exception as exc:  # Catch unexpected unhandled exceptions
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update profile: {str(exc)}")  # Return stable 500 error format