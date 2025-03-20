from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from src.core.config import settings

engine = create_async_engine(
    settings.db.dsn,
    echo=settings.db.show_query,
    future=True,
    )
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


async def get_db_session() -> AsyncSession:
    """
    Получение асинхронной сессии базы данных
    """
    async with async_session_maker() as session:
        yield session