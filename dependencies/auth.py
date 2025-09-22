import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, WebSocket, WebSocketException, status
from fastapi.security import APIKeyHeader

from services.redis_setup import redis_client

JWT_SECRET = os.getenv("JWT_SECRET", "Zealous")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')
api_key_scheme = APIKeyHeader(name="Authorization")


async def register_user(username: str, password: str) -> str:
    try:
        user_exists = await redis_client.exists(f"user:{username}")
        if user_exists:
            print(f"User '{username}' already exists.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        await redis_client.hset(
            f"user:{username}",
            mapping={
                "hashed_password": hashed_password.decode("utf-8"),
            },
        )

        print(f"User '{username}' registered successfully.")
        token = create_token(username)
        return {
            "message": f"User '{username}' registered successfully.",
            "access_token": token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred during registration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)


async def login_user(username=str, password=str) -> dict:
    try:
        user_data = await redis_client.hgetall(f"user:{username}")

        if not user_data:
            print(f"User '{username}' does not exist.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' does not exist.",
            )

        stored_password_hash = user_data.get("hashed_password")
        if not stored_password_hash:
            print(f"User '{username}' has no stored password hash.")
            return False

        if bcrypt.checkpw(
            password.encode("utf-8"), stored_password_hash.encode("utf-8")
        ):
            token = create_token(username)
            return {"access_token": token, "token_type": "bearer"}
        else:
            print(f"Invalid password for user '{username}'.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid password for user '{username}'.",
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred during registration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validate_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    return authorization.split(" ", 1)[1].strip()


def get_current_user(authorization: str = Depends(api_key_scheme)) -> str:
    token = extract_bearer(authorization)
    username = validate_token(token)
    return {"username": username}


async def get_user_from_websocket(websocket: WebSocket, token: str) -> str:
    try:
        username = validate_token(token)
        return username
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
