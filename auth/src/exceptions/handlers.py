from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from src.exceptions.auth import AuthException
from src.exceptions.crud import CrudException

def register_exception_handlers(app: FastAPI):
    """
    Регистрирует обработчики исключений в приложении FastAPI
    """

    # Обработчик исключений для пользовательских ошибок аутентификации
    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    # Обработчик исключений для пользовательских ошибок CRUD-операций
    @app.exception_handler(CrudException)
    async def crud_exception_handler(request: Request, exc: CrudException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
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