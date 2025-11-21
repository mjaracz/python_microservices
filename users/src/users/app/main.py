from shared.messagebus import EventHandler, start_worker_sync
from shared.database.postgres import create_postgres_pool
from jose import jwt
import os
from .repository import UsersRepository

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://users:users_pass@postgres_users:5432/usersdb")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwt")
ALGORITHM = "HS256"

SessionLocal = create_postgres_pool(DATABASE_URL)
repo = UsersRepository(SessionLocal)

@EventHandler("user.register")
async def handle_register(payload):
    uid = await repo.register_user(payload["email"], payload["password"])
    token = jwt.encode({"user_id": uid}, JWT_SECRET, algorithm=ALGORITHM)
    return {"ok": True, "user_id": uid, "token": token}

@EventHandler("user.login")
async def handle_login(payload):
    uid = await repo.authenticate_user(payload["email"], payload["password"])
    if not uid:
        return {"ok": False, "error": "invalid_credentials"}
    token = jwt.encode({"user_id": uid}, JWT_SECRET, algorithm=ALGORITHM)
    return {"ok": True, "user_id": uid, "token": token}

if __name__ == "__main__":
    start_worker_sync()
