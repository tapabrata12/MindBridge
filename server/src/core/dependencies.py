# File: server/src/core/dependencies.py  # Full file path comment as requested

from typing import Any
from fastapi import Depends, HTTPException, status  # Import dependency system and HTTP error helpers
from fastapi.security import OAuth2PasswordBearer  # Import bearer-token extractor for protected routes
from pymongo.errors import PyMongoError
from src.core.config import settings  # Import app settings for API prefix values
from src.core.security import decode_token  # Import JWT decoding/verification helper
from src.db import mongodb  # Import MongoDB database handle module

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.PREFIX}/auth/login/swagger")  # Define token URL for Swagger authorize flow


def _credentials_exception(detail: str) -> HTTPException:
    """Build consistent OAuth2-compatible authentication failures."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """Validate an access token and return only safe current-user fields."""

    payload = decode_token(token)  # Decode JWT and verify signature/expiration
    if payload is None:  # Handle invalid or expired JWT
        raise _credentials_exception("Invalid or expired token")

    token_type = payload.get("type")  # Read the explicit JWT type claim from the decoded token
    if token_type != "access":  # Protected routes must only accept short-lived access tokens
        raise _credentials_exception("Access token required")

    email = payload.get("sub")  # Extract subject claim (we store user email here)
    if not isinstance(email, str) or not email.strip():  # Validate subject structure and non-empty value
        raise _credentials_exception("Invalid token payload")

    if mongodb.db is None:  # Make database initialization failure explicit before collection access
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service is temporarily unavailable")

    try:
        user = await mongodb.db[settings.USER_COLLECTION].find_one(
            {"email": email.strip().lower()},
            {"_id": 1, "email": 1, "profile": 1, "refresh_tokens": 1},
        )
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from exc
    if user is None:  # Handle deleted/missing user record case
        raise _credentials_exception("Invalid or expired token")

    if not isinstance(user.get("refresh_tokens"), list):  # Ensure expected DB shape for refresh token list
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service is temporarily unavailable")

    if len(user["refresh_tokens"]) == 0:  # Enforce session validity by requiring active refresh token(s)
        raise _credentials_exception("Session expired, please login again")

    user["_id"] = str(user["_id"])  # Convert Mongo ObjectId to string for JSON-safe downstream usage
    user.pop("refresh_tokens", None)
    return user


# Keep existing route imports working while new modules can use the clearer name.
search_user = get_current_user
