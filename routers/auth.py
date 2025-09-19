import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException

# from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/auth", tags=["Authentication"])

JWT_SECRET = os.getenv("JWT_SECRET", "Zealous")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))

dummy_user = {"Barath": "passwordBarath", "Abi": "passwordAbi"}


def create_token(username: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/login")
def login(username: str, password: str):
    if username not in dummy_user or dummy_user[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(username)
    return {"access token": token, "token-type": "bearer"}
