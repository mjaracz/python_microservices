from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UsersRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def register_user(self, email: str, password: str) -> int:
        hashed = pwd.hash(password)
        async with self.session_factory() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE,
                    hashed_password TEXT
                );
            """)
            result = await session.execute(
                text("""
                INSERT INTO users (email, hashed_password)
                VALUES (:email, :hashed)
                ON CONFLICT (email) DO NOTHING
                RETURNING id;
                """),
                {"email": email, "hashed": hashed},
            )
            await session.commit()
            row = result.first()
            return row[0] if row else None

    async def authenticate_user(self, email: str, password: str):
        async with self.session_factory() as session:
            result = await session.execute(
                text("SELECT id, hashed_password FROM users WHERE email = :email"),
                {"email": email}
            )
            row = result.first()
            if not row:
                return None
            uid, hashed = row
            if not pwd.verify(password, hashed):
                return None
            return uid
