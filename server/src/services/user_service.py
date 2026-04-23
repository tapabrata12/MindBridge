# File: server/src/services/user_service.py  # Full file path comment as requested

from datetime import datetime, timezone  # Import timezone-aware datetime utilities
from typing import Any, Dict, Optional  # Import typing helpers for clearer function contracts
from bson import ObjectId  # Import MongoDB ObjectId converter
from bson.errors import InvalidId  # Import invalid ObjectId error type
from fastapi import HTTPException, status  # Import HTTP exception and status code helpers
from src.core.config import settings  # Import global app settings
from src.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password  # Import security helpers
from src.db import mongodb  # Import MongoDB database module
from src.models.user import create_user  # Import user document factory
from src.schemas.user import TokenResponse, UserProfileResponse, UserProfileUpdate  # Import Pydantic v2 response/update schemas


def _utc_now_iso() -> str:  # Create helper for consistent UTC timestamps
    return datetime.now(timezone.utc).isoformat()  # Return current UTC timestamp in ISO format


async def register_user(email: str, password: str) -> Optional[Dict[str, Any]]:  # Register new user and issue initial token pair
    existing_user = await mongodb.db[settings.USER_COLLECTION].find_one({"email": email})  # Check if user already exists by email
    if existing_user is not None:  # Handle duplicate account case
        return None  # Return None so route can raise 409 Conflict

    hashed_password = hash_password(password)  # Hash plain password with bcrypt before saving
    user_document = create_user(email, hashed_password)  # Build new user document with default profile fields
    await mongodb.db[settings.USER_COLLECTION].insert_one(user_document)  # Insert new user document asynchronously

    access_token = create_access_token({"sub": email})  # Create short-lived access token
    refresh_token = create_refresh_token({"sub": email})  # Create long-lived refresh token
    await mongodb.db[settings.USER_COLLECTION].update_one({"email": email}, {"$push": {"refresh_tokens": refresh_token}, "$set": {"updated_at": _utc_now_iso()}})  # Save refresh token and update timestamp

    return TokenResponse(access_token=access_token, refresh_token=refresh_token).model_dump()  # Return schema-safe token response payload


async def user_login(email: str, password: str) -> Optional[Dict[str, Any]]:  # Authenticate existing user and issue new token pair
    existing_user = await mongodb.db[settings.USER_COLLECTION].find_one({"email": email})  # Fetch user by email
    if existing_user is None:  # Handle unknown email
        return None  # Return None so route can raise 401 Unauthorized

    is_password_valid = verify_password(password, existing_user["hash_password"])  # Compare provided password with bcrypt hash
    if not is_password_valid:  # Handle wrong password
        return None  # Return None so route can raise 401 Unauthorized

    access_token = create_access_token({"sub": email})  # Issue fresh access token after successful auth
    refresh_token = create_refresh_token({"sub": email})  # Issue fresh refresh token after successful auth
    await mongodb.db[settings.USER_COLLECTION].update_one({"email": email}, {"$push": {"refresh_tokens": refresh_token}, "$set": {"updated_at": _utc_now_iso()}})  # Track refresh token server-side and update timestamp

    return TokenResponse(access_token=access_token, refresh_token=refresh_token).model_dump()  # Return structured token payload


async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:  # Rotate refresh token and mint fresh access token
    decoded_payload = decode_token(refresh_token)  # Decode incoming refresh token and verify signature/expiry
    if decoded_payload is None:  # Handle invalid or expired refresh token
        return None  # Return None so route can raise 401 Unauthorized

    email = decoded_payload.get("sub")  # Extract email from token subject claim
    if not isinstance(email, str) or not email.strip():  # Validate subject claim integrity
        return None  # Return None for malformed payload

    user = await mongodb.db[settings.USER_COLLECTION].find_one({"email": email})  # Fetch user document tied to refresh token subject
    if user is None:  # Handle missing user document
        return None  # Return None for invalid refresh flow

    current_tokens = user.get("refresh_tokens", [])  # Read server-side refresh token list
    if refresh_token not in current_tokens:  # Check token revocation/reuse protection
        return None  # Return None when token is not active anymore

    new_access_token = create_access_token({"sub": email})  # Mint new access token for continued API use
    new_refresh_token = create_refresh_token({"sub": email})  # Mint brand-new refresh token for rotation strategy

    await mongodb.db[settings.USER_COLLECTION].update_one(  # Atomically rotate refresh token in database
        {"email": email},  # Match current user by email
        {  # Start update operations block
            "$pull": {"refresh_tokens": refresh_token},  # Remove old refresh token so it cannot be reused
            "$push": {"refresh_tokens": new_refresh_token},  # Add newly issued refresh token as active token
            "$set": {"updated_at": _utc_now_iso()},  # Stamp update time for auditability
        },  # End update operations block
    )  # Finish async database update

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token).model_dump()  # Return rotated token pair to client


async def get_user_and_delete_refresh_token(email: str) -> bool | str:  # Revoke all active sessions for a user
    if not isinstance(email, str) or not email.strip():  # Validate email input shape
        return False  # Return False for invalid function input

    user = await mongodb.db[settings.USER_COLLECTION].find_one({"email": email})  # Find user by email
    if user is None:  # Handle user not found path
        return False  # Return False so route can return 404

    if not user.get("refresh_tokens"):  # Check if user already has no active sessions
        return "Already logged out"  # Return idempotent state message

    await mongodb.db[settings.USER_COLLECTION].update_one({"email": email}, {"$set": {"refresh_tokens": [], "updated_at": _utc_now_iso()}})  # Revoke all sessions and update timestamp
    return True  # Return success flag for logout response


async def user_profile_update(user_id: str, profile_details: UserProfileUpdate) -> UserProfileResponse:  # Update authenticated user's profile document
    try:  # Start ObjectId conversion validation
        object_id = ObjectId(user_id)  # Convert incoming string user ID into Mongo ObjectId
    except InvalidId:  # Catch invalid ID format
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")  # Raise 400 for malformed ID

    update_result = await mongodb.db[settings.USER_COLLECTION].update_one({"_id": object_id}, {"$set": {"profile": profile_details.model_dump(), "updated_at": _utc_now_iso()}})  # Persist profile update and timestamp
    if update_result.matched_count == 0:  # Check if target user existed
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")  # Raise 404 when user is missing

    updated_user = await mongodb.db[settings.USER_COLLECTION].find_one({"_id": object_id})  # Read back user after update
    if updated_user is None or not updated_user.get("profile"):  # Validate profile exists after update
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated profile")  # Raise 500 for unexpected persistence/read issue

    return UserProfileResponse.model_validate(updated_user["profile"])  # Return validated profile response model


async def get_user_profile(user_id: str) -> UserProfileResponse:  # Fetch authenticated user's profile document
    try:  # Start ObjectId conversion validation
        object_id = ObjectId(user_id)  # Convert incoming user ID to Mongo ObjectId
    except InvalidId:  # Catch invalid ID type/format
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")  # Raise 400 for invalid user ID

    user = await mongodb.db[settings.USER_COLLECTION].find_one({"_id": object_id})  # Fetch user document by ID
    if user is None:  # Handle missing user case
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")  # Raise 404 when user record does not exist

    profile_data = user.get("profile")  # Extract profile subdocument
    if not profile_data:  # Handle empty/missing profile case
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")  # Raise 404 when profile is not yet completed

    return UserProfileResponse.model_validate(profile_data)  # Return schema-validated profile data