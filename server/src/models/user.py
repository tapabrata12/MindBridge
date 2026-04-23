# File: server/src/models/user.py  # Full file path comment as requested

from datetime import datetime, timezone  # Import timezone-aware datetime tools for consistent timestamps
from typing import Any, Dict, List  # Import typing helpers for structured MongoDB document shapes


def _utc_now_iso() -> str:  # Create helper function for UTC ISO timestamp generation
    return datetime.now(timezone.utc).isoformat()  # Return current UTC time as ISO-8601 string


def _default_profile() -> Dict[str, Any]:  # Create helper function to build default profile payload
    return {  # Return default profile dictionary
        "age": None,  # Initialize age as unknown
        "gender": None,  # Initialize gender as unknown
        "occupation": None,  # Initialize occupation as unknown
        "sleep_hours": None,  # Initialize sleep-hours baseline as unknown
        "social_support": None,  # Initialize social support baseline as unknown
        "life_events": [],  # Initialize life-events list as empty
    }  # End default profile dictionary


def _default_session() -> Dict[str, Any]:  # Create helper function to build default session metadata
    return {  # Return session metadata dictionary
        "last_login_at": None,  # Track latest login time (set during login flow)
        "last_password_change_at": None,  # Track latest password change time for security workflows
        "failed_login_attempts": 0,  # Initialize failed login counter for lockout/risk controls
        "is_locked": False,  # Initialize account lock state
    }  # End default session metadata dictionary


def create_user(email: str, hash_password: str) -> Dict[str, Any]:  # Build new user MongoDB document from validated inputs
    now_iso = _utc_now_iso()  # Capture one consistent creation timestamp for this document
    return {  # Return complete user document payload
        "email": email,  # Store normalized user email
        "hash_password": hash_password,  # Store bcrypt-hashed password (never plain password)
        "profile": _default_profile(),  # Attach default profile object for onboarding/personalization
        "refresh_tokens": [],  # Initialize active refresh token list for session revocation support
        "session": _default_session(),  # Attach session metadata object for auth observability/security
        "roles": ["user"],  # Assign default role list (future-ready for RBAC expansion)
        "is_active": True,  # Mark account as active by default
        "created_at": now_iso,  # Record account creation timestamp
        "updated_at": now_iso,  # Record initial update timestamp equal to creation time
    }  # End user document payload