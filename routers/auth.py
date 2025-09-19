import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketException, status

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


def validate_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithm=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def getUserFromWebsocket(websocket: WebSocket, token: str):
    try:
        username = validate_token(token)
        return username
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)


@router.post("/login")
def login(username: str, password: str):
    if username not in dummy_user or dummy_user[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(username)
    return {"access token": token, "token-type": "bearer"}
