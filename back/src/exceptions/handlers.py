from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from src.exceptions.request import RequestException


def register_exception_handlers(app: FastAPI):
    """
    Регистрирует обработчики исключений в приложении FastAPI
    """

    # Обработчик исключений для ошибок запросов
    @app.exception_handler(RequestException)
    async def request_exception_handler(request: Request, exc: RequestException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": exc.message,
                "detail": exc.details,
                },
        )

    # Обработчик общего исключения
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "path": str(request.url),
            },
        )