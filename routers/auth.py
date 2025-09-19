import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies.auth import create_token, get_current_user

# from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/auth", tags=["Authentication"])

JWT_SECRET = os.getenv("JWT_SECRET", "Zealous")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))

dummy_user = {"Barath": "123", "Abi": "123"}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    username: str


@router.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest):
    username = login_request.username
    password = login_request.password
    if username not in dummy_user or dummy_user[username] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_token(username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}
