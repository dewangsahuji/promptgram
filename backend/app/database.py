from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

from sqlalchemy.orm import DeclarativeBase
from app.config import settings



Base = declarative_base()

# class Base(DeclarativeBase):
#     pass


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10, 
    max_overflow=20, 
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    # autocommit=False,
    expire_on_commit=False
)


# Dependency to inject the DB session into your routers
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


