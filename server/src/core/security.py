from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

from src.core.config import settings

crypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

"""
For password hashing 
    Args: password: type -> String
    Return hash password: type -> String
"""
def hash_password(password: str)-> str:
    return crypt_context.hash(password)

"""
For password verifying
    Args: plain password type -> String | hashed_password type -> String
    Return boolean Expression: type -> Bool
"""
def verify_password(plain_password: str, hashed_password: str)-> bool:
    return crypt_context.verify(plain_password, hashed_password)

"""
Creating access token using User's data
    Args: Data: type -> Dictionary
    Return Expression: type -> String
"""

def create_access_token(data: dict)-> str:
    copied_data = data.copy()
    expire_time = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    copied_data.update({'exp': expire_time})
    return jwt.encode(copied_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

"""
Creating refresh token using User's data
    Args: Data: type -> Dictionary
    Return boolean Expression: type -> String
"""

def create_refresh_token(data: dict)-> str:
    copied_data = data.copy()
    expire_time = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    copied_data.update({'exp': expire_time})
    return jwt.encode(copied_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

"""
Creating decode token
    Args: token: type -> String
    Return User data: type -> Dictionary
"""

def decode_token(token: str)-> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=settings.JWT_ALGORITHM)
        return payload
    except JWTError:
        return None