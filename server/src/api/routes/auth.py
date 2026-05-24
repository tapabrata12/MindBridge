# File: server/src/api/routes/auth.py  # Full file path comment at top

from typing import Any, Dict  # Import typing helpers for dictionary response types
from fastapi import APIRouter, Depends, HTTPException, status  # Import FastAPI router, dependency, and HTTP error/status tools
from fastapi.security import OAuth2PasswordRequestForm  # Import form schema for Swagger login
from src.core.config import settings  # Import app settings to read API prefix
from src.core.dependencies import search_user  # Import dependency that gets current logged-in user from token
from src.schemas.user import RefreshRequest, TokenResponse, UserCreate, UserLogin, UserResponse  # Import request/response schemas
from src.services.user_service import get_user_and_delete_refresh_token, refresh_access_token, register_user, user_login  # Import service functions

router = APIRouter(prefix=f"{settings.PREFIX}/auth", tags=["Authentication"])  # Create auth router with /api/auth prefix


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)  # Create register endpoint
async def register(user: UserCreate) -> TokenResponse:  # Define async register function with typed input/output
    result = await register_user(user.email, user.password)  # Call service to create user and generate tokens
    if result is None:  # Check if service says user already exists
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")  # Return 409 for duplicate user
    return TokenResponse(**result)  # Return token response model from service payload


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)  # Create login endpoint
async def login(user: UserLogin) -> TokenResponse:  # Define async login function with typed request/response
    result = await user_login(user.email, user.password)  # Call service to verify credentials and issue tokens
    if result is None:  # Check wrong email/password case
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")  # Return 401 on auth failure
    return TokenResponse(**result)  # Return token pair on success


@router.post("/login/swagger", response_model=TokenResponse, status_code=status.HTTP_200_OK)  # Create Swagger-only login endpoint
async def login_swagger(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:  # Use OAuth2 form data (username/password)
    result = await user_login(form_data.username, form_data.password)  # Reuse normal login service logic
    if result is None:  # Check invalid credentials case
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")  # Return 401 if login fails
    return TokenResponse(**result)  # Return same token schema for consistency


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)  # Create current-user endpoint
async def get_me(user: Dict[str, Any] = Depends(search_user)) -> UserResponse:  # Resolve user from JWT dependency
    email = user.get("email")  # Read email from dependency result
    if not isinstance(email, str) or not email.strip():  # Validate email exists in dependency output
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please login first")  # Return 401 if token context invalid
    return UserResponse(email=email)  # Return only safe user field


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)  # Create refresh-token endpoint
async def refresh_token(payload: RefreshRequest) -> TokenResponse:  # Accept refresh token request body
    result = await refresh_access_token(payload.refresh_token)  # Call service to validate and rotate token
    if result is None:  # Check invalid or expired refresh token
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")  # Return 401 for bad refresh token
    return TokenResponse(**result)  # Return refreshed token response


@router.post("/logout", status_code=status.HTTP_200_OK)  # Create logout endpoint
async def logout(user: Dict[str, Any] = Depends(search_user)) -> Dict[str, str]:  # Use authenticated user from dependency
    email = user.get("email")  # Extract email from current user context
    if not isinstance(email, str) or not email.strip():  # Validate email before service call
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please login first")  # Return 401 if not authenticated
    result = await get_user_and_delete_refresh_token(email)  # Revoke refresh tokens for this user
    if result is False:  # Check user-not-found failure case
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")  # Return 404 when user record missing
    if result == "Already logged out":  # Check idempotent logout case
        return {"message": "Already logged out"}  # Return friendly message when no active session exists
    return {"message": "Successfully logged out"}  # Return success message on logout