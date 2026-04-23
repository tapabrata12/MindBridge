from fastapi import APIRouter,Depends,HTTPException,status
from typing import Dict
from src.core.dependencies import search_user
from src.services.user_service import get_user_profile,user_profile_update
from src.schemas.user import UserProfileResponse,UserProfileUpdate
from src.core.config import settings
router = APIRouter(prefix= settings.PREFIX + '/profile', tags=['Profile'])

@router.post('/profile', response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(profile_update: UserProfileUpdate , user: Dict = Depends(search_user)):
    """
        Update user profile (onboarding data).
        Protected by JWT - only the logged-in user can update their own profile.
        """
    # current_user comes from JWT decode - it contains "_id" as string

    try:
        updated_profile =  await user_profile_update(user['_id'], profile_update)
        return updated_profile

    except HTTPException:
        raise  # Re-raise service exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.get('/profile', response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(user: Dict = Depends(search_user)):
    """
        Get current user's profile.
        Returns 404 if profile not yet filled (onboarding pending).
        """
    if not user.get("_id") or user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user token"
        )
    try:
        profile: UserProfileResponse = await get_user_profile(user['_id'])
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please complete onboarding."
            )
        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )