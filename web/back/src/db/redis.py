from typing import Optional
from redis.asyncio import Redis

# Глобальная переменная для хранения подключения к Redis
redis: Optional[Redis] = None


async def get_redis() -> Redis | None:
    """
    Функция для получения текущего подключения к Redis
    """

    return redis