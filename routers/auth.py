from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies.auth import get_current_user, login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

dummy_users = {"Barath": "123", "Abi": "123"}


class AuthRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    username: str


@router.post("/register")
async def register(register_request: AuthRequest):
    username = register_request.username
    password = register_request.password

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Username and password missing",
        )

    response = await register_user(username, password)
    return response


@router.post("/login", response_model=TokenResponse)
async def login(login_request: AuthRequest):
    username = login_request.username
    password = login_request.password
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Username and password missing",
        )
    response = await login_user(username, password)
    return response


@router.get("/me", response_model=UserResponse)
def me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}
