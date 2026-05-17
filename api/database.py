import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

# We need the asyncpg driver for async operations
# e.g. postgresql+asyncpg://nexus:password@localhost:5432/nexusai
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://nexus:password@localhost:5432/nexusai")

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
