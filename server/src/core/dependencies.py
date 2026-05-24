# File: server/src/core/dependencies.py  # Full file path comment as requested

from typing import Any, Dict  # Import typing helpers for structured user return values
from fastapi import Depends, HTTPException, status  # Import dependency system and HTTP error helpers
from fastapi.security import OAuth2PasswordBearer  # Import bearer-token extractor for protected routes
from src.core.config import settings  # Import app settings for API prefix values
from src.core.security import decode_token  # Import JWT decoding/verification helper
from src.db import mongodb  # Import MongoDB database handle module

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.PREFIX}/auth/login/swagger")  # Define token URL for Swagger authorize flow


async def search_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:  # Build reusable async dependency to resolve authenticated user
    if not token:  # Validate token presence defensively
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")  # Return 401 when no token is provided

    payload = decode_token(token)  # Decode JWT and verify signature/expiration
    if payload is None:  # Handle invalid or expired JWT
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")  # Return 401 for bad token

    token_type = payload.get("type")  # Read the explicit JWT type claim from the decoded token
    if token_type != "access":  # Protected routes must only accept short-lived access tokens
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token required")  # Reject refresh tokens on protected routes

    email = payload.get("sub")  # Extract subject claim (we store user email here)
    if not isinstance(email, str) or not email.strip():  # Validate subject structure and non-empty value
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")  # Return 401 for malformed JWT payload

    if mongodb.db is None:  # Make database initialization failure explicit before collection access
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection is not initialized")  # Return stable 500 when app startup did not initialize MongoDB

    user = await mongodb.db[settings.USER_COLLECTION].find_one({"email": email})  # Fetch user document by JWT subject email
    if user is None:  # Handle deleted/missing user record case
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")  # Return 401 to avoid leaking account existence details

    if not isinstance(user.get("refresh_tokens"), list):  # Ensure expected DB shape for refresh token list
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid user token store")  # Return 500 for corrupted data structure

    if len(user["refresh_tokens"]) == 0:  # Enforce session validity by requiring active refresh token(s)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please login again")  # Return 401 when session has been revoked

    user["_id"] = str(user["_id"])  # Convert Mongo ObjectId to string for JSON-safe downstream usage
    user.pop("hash_password", None)  # Remove password hash from dependency output for safer route consumption
    return user  # Return sanitized authenticated user object to protected endpoints
