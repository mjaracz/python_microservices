from jose import JWTError, jwt
from fastapi import WebSocket, HTTPException
import os

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwt")
ALGORITHM = "HS256"

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def ws_authenticate(websocket: WebSocket) -> dict:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        raise HTTPException(status_code=401, detail="Missing token")
    payload = decode_token(token)
    return payload
