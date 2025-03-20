import httpx
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from src.core.config import settings
from src.schemas.auth import UserJWT, UserSchema
from src.utils.token import JWTHelper


class AuthService(HTTPBearer):
    """
    Сервис аутентификации для проверки JWT-токена
    """

    def __init__(self, use_remote_auth: bool = False, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.verify_url = settings.auth.verify_url
        self.use_remote_auth = use_remote_auth

    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code.",
            )
        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )

        token = credentials.credentials

        if self.use_remote_auth:
            return await self.verify_jwt_token(token)
        else:
            return self.parse_token(token)

    @staticmethod
    def parse_token(token: str) -> UserJWT:
        """
        Декодирует токен и возвращает объект UserJWT, если он валиден
        """
        user_data = JWTHelper.decode(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired token",
            )
        return user_data

    async def verify_jwt_token(self, token: str) -> UserSchema:
        """
        Проверяет JWT-токен через удаленный сервис авторизации
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(self.verify_url, json={"token": token})

        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        return response.json()