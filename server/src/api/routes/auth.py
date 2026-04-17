from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from src.core.config import settings
from src.schemas.user import UserCreate,UserLogin, UserResponse, TokenResponse,RefreshRequest
from src.services.user_service import register_user, user_login, refresh_access_token,get_user_and_delete_refresh_token
from src.core.dependencies import search_user

router = APIRouter(prefix=settings.PREFIX + '/auth', tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    result = await register_user(user.email, user.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "User successfully registered", "content": result})

@router.post("/login",response_model=TokenResponse)
async def login(user: UserLogin):
    result = await user_login(user.email, user.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User successfully logged in", "content": result})

@router.post("/login/swagger",summary="Login a user", description="This is spacial Login route only for swagger UI",response_description="Returns access and refresh token",response_model=TokenResponse)
async def test_login(form_data: OAuth2PasswordRequestForm = Depends()):
    result = await user_login(form_data.username, form_data.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return result

@router.get('/profile', response_model=UserResponse)
async def get_user(user=Depends(search_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Please login first")
    return JSONResponse(status_code=status.HTTP_200_OK, content=user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token: RefreshRequest):
    result = await refresh_access_token(token.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    return result

@router.get("/logout")
async def logout(user =  Depends(search_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Please login first")

    success = await get_user_and_delete_refresh_token(user['email'])

    if not success:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,content={"message": "You are not logged in"})

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"Token deletion {success}. You have successfully logged out"})