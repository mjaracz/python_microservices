from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

def create_postgres_pool(url: str):
    # Accept URLs like postgresql+psycopg://...
    engine = create_async_engine(url, future=True)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
