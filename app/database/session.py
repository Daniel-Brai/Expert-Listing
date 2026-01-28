import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from core.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

engine = create_async_engine(
    url=DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=0,
    json_serializer=lambda obj: json.dumps(obj),
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()


db_session_manager = asynccontextmanager(get_db_session)
