import uvicorn
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from src.db import redis
from src.core.config import settings
from src.core.logger import LOGGING
from src.api.v1 import ping, auth, user
from src.exceptions.handlers import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения FastAPI.
    Создает подключение к Redis при старте приложения и закрывает его при завершении
    """
    redis.redis = Redis(host=settings.redis.host, port=settings.redis.port)
    yield
    await redis.redis.close()


# Инициализация FastAPI-приложения
app = FastAPI(
    lifespan=lifespan, # Указание жизненного цикла приложения
    version="0.0.1", # Версия приложения
    title=settings.project_name, # Название приложения
    description=settings.project_description, # Описание приложения
    docs_url="/ugc/api/openapi", # URL для документации Swagger
    openapi_url="/ugc/api/openapi.json", # URL для OpenAPI схемы
    default_response_class=ORJSONResponse, # Быстрая обработка JSON с ORJSON
)

# Регистрация обработчиков исключений
register_exception_handlers(app)

# Подключение роутера для проверки доступности сервера
app.include_router(ping.router, prefix="/api/v1", tags=["ping"])
# Подключение роутера для работы с аутентификацией
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
# Подключение роутера для работы с пользователями
app.include_router(user.router, prefix="/api/v1", tags=["user"])


# Точка входа в приложение
if __name__ == "__main__":
    # Запуск Uvicorn-сервера
    uvicorn.run(
        "main:app",  # Указание приложения (main.py:app)
        host=settings.default_host,  # Хост из настроек
        port=settings.default_port,  # Порт из настроек
        log_config=LOGGING,  # Конфигурация логирования
        log_level=logging.INFO,  # Уровень логирования
        reload=True,  # Автоматическая перезагрузка при изменении файлов
    )