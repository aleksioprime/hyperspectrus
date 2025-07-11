from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import create_engine, orm

from src.core.config import settings

engine = create_async_engine(
    settings.db.dsn,
    echo=settings.db.show_query,
    future=True,
    )

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Получение асинхронной сессии базы данных
    """
    async with async_session_maker() as session:
        yield session


sync_engine = create_engine(
    settings.db.dsn.replace("+asyncpg", ""),
    echo=settings.db.show_query,
    future=True,
)

SyncSessionLocal = orm.sessionmaker(sync_engine, expire_on_commit=False)