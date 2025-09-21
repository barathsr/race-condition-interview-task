from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies.auth import create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

dummy_users = {"Barath": "123", "Abi": "123"}


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
    if username not in dummy_users or dummy_users[username] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_token(username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}
