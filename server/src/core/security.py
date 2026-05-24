# File: server/src/core/security.py  # Full file path comment as requested

from datetime import datetime, timedelta, timezone  # Import timezone-aware datetime utilities for secure token expiry
from typing import Any, Dict, Optional  # Import typing helpers for token payload contracts
from jose import JWTError, jwt  # Import python-jose tools for JWT encode/decode
from passlib.context import CryptContext  # Import passlib bcrypt context for password hashing
from src.core.config import settings  # Import app settings for JWT secret, algorithm, and TTL values

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Configure bcrypt hashing strategy for password operations


def hash_password(password: str) -> str:  # Create helper to hash plain text passwords securely
    return pwd_context.hash(password)  # Return bcrypt hash string for storage in database


def verify_password(plain_password: str, hashed_password: str) -> bool:  # Create helper to compare plain password with stored hash
    return pwd_context.verify(plain_password, hashed_password)  # Return True when password matches hash, else False


def _build_token_payload(data: Dict[str, Any], expires_delta: timedelta, token_type: str) -> Dict[str, Any]:  # Internal helper to build consistent JWT payloads
    payload = data.copy()  # Copy caller data to avoid mutating external dictionaries
    payload["exp"] = datetime.now(timezone.utc) + expires_delta  # Add timezone-aware expiration claim
    payload["type"] = token_type  # Add explicit token type claim (access or refresh)
    payload["iat"] = datetime.now(timezone.utc)  # Add issued-at claim for audit and debugging usefulness
    return payload  # Return finalized token payload dictionary


def create_access_token(data: Dict[str, Any]) -> str:  # Create short-lived access token for API authorization
    payload = _build_token_payload(data=data, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), token_type="access")  # Build standardized access payload
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)  # Encode and sign access JWT


def create_refresh_token(data: Dict[str, Any]) -> str:  # Create long-lived refresh token for session continuation
    payload = _build_token_payload(data=data, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), token_type="refresh")  # Build standardized refresh payload
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)  # Encode and sign refresh JWT


def decode_token(token: str) -> Optional[Dict[str, Any]]:  # Decode and verify any JWT token safely
    try:  # Start controlled decode block
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])  # Decode token using configured secret and allowed algorithm list
        return payload  # Return decoded payload dictionary on success
    except JWTError:  # Catch signature, expiration, and malformed token failures
        return None  # Return None so caller can handle as unauthorized