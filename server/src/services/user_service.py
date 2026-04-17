from src.core.config import settings
from src.db import mongodb
from src.models.user import create_user
from src.schemas.user import TokenResponse
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)

async def register_user(email: str, password: str)-> dict | None:
    """
    Check if the user exists if exists then return None means user exists
    if user doesn't exist then:
    1. Hash the given password
    2. Create a new user
    3. Save it to the database
    """
    existed_user = await mongodb.db[settings.USER_COLLECTION].find_one({'email': email})
    if existed_user:
        return None

    hashed_password = hash_password(password)
    user = create_user(email, hashed_password)

    await mongodb.db[settings.USER_COLLECTION].insert_one(user)

    access_token = create_access_token({'sub': email})
    refresh_token = create_refresh_token({'sub': email})

    await mongodb.db[settings.USER_COLLECTION].update_one(
        {"email": email},
        {"$push": {"refresh_tokens": refresh_token}},
    )

    return TokenResponse(access_token=access_token,refresh_token=refresh_token).model_dump()

async def user_login(email: str, password: str)-> dict | None:
    """
      Check if user doesn't exist then return None
      if the user exists then:
      1. verify the password of not ok then return None if ok then:
      2. Create access token and refresh token
      3. Save the refresh token to the database
      4. Return the access token and refresh token
      """
    existed_user = await mongodb.db[settings.USER_COLLECTION].find_one({'email': email})
    if not existed_user:
        return None
    check_password = verify_password(password, existed_user["hash_password"])

    if not check_password:
        return None

    access_token = create_access_token({'sub': email})
    refresh_token = create_refresh_token({'sub': email})

    await mongodb.db[settings.USER_COLLECTION].update_one(
        {"email": email},
        {"$push": {"refresh_tokens": refresh_token}},
    )

    return TokenResponse(access_token=access_token,refresh_token=refresh_token).model_dump()

async def refresh_access_token(refresh_token: str) -> dict | None:
    """
    Step 1: Verify refresh token signature is valid
    Step 2: Extract email from token payload
    Step 3: Check that email exists in DB
    Step 4: Check that refresh token exists in DB (revocation check)
    """

    # Step 1 — decode and verify signature
    decoded_refresh_token = decode_token(refresh_token)
    if decoded_refresh_token is None:
        return None

    # Step 2 — extract email
    email = decoded_refresh_token.get("sub")
    if not email:
        return None

    # Step 3 — check user exists in DB
    user = await mongodb.db[settings.USER_COLLECTION].find_one({"email": email})
    if not user:
        return None

    # Step 4 — check refresh token exists in DB (not revoked)
    if refresh_token not in user.get("refresh_tokens", []):
        return None

    # All checks passed — issue new access token
    new_access_token = create_access_token({"sub": email})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token
    ).model_dump()





async def get_user_and_delete_refresh_token(email: str)-> bool | str:

    """

    Step 1: Verify user exists
    Step 2: Check that if the "refresh_tokens" array already empty or not if yes then return None
    Step 3: Update the array to []
    Step 4: Return successful message

    :param email:
    :return: successful | None
    """
    if not email:
        return False
    user = await mongodb.db[settings.USER_COLLECTION].find_one({'email':email})
    if not user:
        return False

    if not user.get("refresh_tokens"):
        return "Already logged out"

    await mongodb.db[settings.USER_COLLECTION].update_one(
        {"email": email},  # FILTER — find this user
        {"$set": {"refresh_tokens": []}}  # UPDATE — replace with an empty array
    )

    return True
