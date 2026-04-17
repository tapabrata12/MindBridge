from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException,status

from src.core.security import decode_token
from src.core.config import settings
from src.db import mongodb

# This `tokenUrl` ONLY affects Swagger UI's Authorize button location
# It does NOT change how your routes work
search_token_schema = OAuth2PasswordBearer(tokenUrl=settings.PREFIX + "/auth/login/swagger")

async def search_user(token: str = Depends(search_token_schema)):

    """
    :param token:
    :return: dict
    Step 1: Check if token is available or not
    Step 2: Check if token is decodable or not
    Step 3: Check if email under that decodable token is available or not
    Step 4: Check if any user with that email exists or not
    Step 5: Convert the '_id' into String and save it to the user
    Step 6: Return the user
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Please login again")

    payload = decode_token(token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired token")

    email = payload['sub']
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token payload")

    user = await mongodb.db[settings.USER_COLLECTION].find_one({"email":email})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user['_id'] = str(user['_id'])

    return user