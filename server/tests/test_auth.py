import pytest  # Import pytest so tests can assert raised FastAPI exceptions.
from fastapi import HTTPException  # Import HTTPException to check protected-route auth failures.
from src.core.dependencies import search_user  # Import the protected-route dependency under test.
from src.core.security import create_access_token, create_refresh_token, decode_token  # Import JWT helpers to create and inspect test tokens.


def test_token_helpers_mark_access_and_refresh_types() -> None:  # Check that generated JWTs include their explicit token type.
    access_payload = decode_token(create_access_token({"sub": "test@example.com"}))  # Create and decode an access token for a test user.
    refresh_payload = decode_token(create_refresh_token({"sub": "test@example.com"}))  # Create and decode a refresh token for the same user.

    assert access_payload is not None  # Confirm the access token decoded successfully.
    assert refresh_payload is not None  # Confirm the refresh token decoded successfully.
    assert access_payload["type"] == "access"  # Confirm access tokens are labeled as access tokens.
    assert refresh_payload["type"] == "refresh"  # Confirm refresh tokens are labeled as refresh tokens.


@pytest.mark.asyncio  # Tell pytest this async test should run inside an event loop.
async def test_search_user_rejects_refresh_tokens_before_database_lookup() -> None:  # Ensure refresh tokens cannot authorize protected routes.
    refresh_token = create_refresh_token({"sub": "test@example.com"})  # Build a valid refresh token that should not be accepted as authorization.

    with pytest.raises(HTTPException) as exc_info:  # Capture the FastAPI exception raised by the dependency.
        await search_user(refresh_token)  # Call the dependency directly with the refresh token.

    assert exc_info.value.status_code == 401  # Confirm the dependency rejects the token as unauthorized.
    assert exc_info.value.detail == "Access token required"  # Confirm the failure reason is specific and clear.
