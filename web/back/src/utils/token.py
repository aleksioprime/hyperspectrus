import time
from datetime import timedelta
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, decode

from src.core.config import settings
from src.core.schemas import UserJWT
from src.models.user import User
from src.exceptions.base import BaseException
from src.utils.time import get_current_utc_time


class JWTHelper:
    """
    Класс для работы с JWT токенами
    """

    @staticmethod
    def create_token(user_id: str, roles: list[str], expiration: timedelta, is_superuser: bool = False) -> str:
        """
        Создает JWT токен
        """
        now = get_current_utc_time()
        payload = {
            'sub': user_id,                 # Идентификатор пользователя
            'iat': now,                     # Время создания токена
            'exp': now + expiration,        # Время истечения токена
            'roles': roles,                 # Роли пользователя
            'is_superuser': is_superuser,   # Пользователь - суперпользователь
        }

        encoded_jwt = jwt.encode(payload, key=settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
        return encoded_jwt

    def generate_token_pair(self, user: User, roles: list[str]) -> tuple[str, str]:
        """
        Генерирует пару access и refresh токенов
        """
        user_id = str(user.id)
        is_superuser = getattr(user, "is_superuser", False)

        access_token = self.create_token(
            user_id=user_id,
            roles=roles,
            is_superuser=is_superuser,
            expiration=settings.jwt.access_token_expire_time,
        )
        refresh_token = self.create_token(
            user_id=user_id,
            roles=roles,
            is_superuser=is_superuser,
            expiration=settings.jwt.refresh_token_expire_time,
        )
        return access_token, refresh_token

    def verify(self, token: str) -> dict:
        """
        Проверяет подлинность JWT токена
        """
        try:
            payload = jwt.decode(
                jwt=token,
                key=settings.jwt.secret_key,
                algorithms=[settings.jwt.algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise BaseException('Token has expired')
        except jwt.InvalidTokenError:
            raise BaseException('Invalid token')

        return payload

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Обновляет access токен с использованием действующего refresh токена
        """
        payload = self.verify(refresh_token)

        user_id = payload['sub']
        roles = payload.get('roles', [])
        is_superuser = payload.get('is_superuser', False)

        new_access_token = self.create_token(
            user_id=user_id,
            roles=roles,
            is_superuser=is_superuser,
            expiration=settings.jwt.access_token_expire_time,
        )

        return new_access_token

    @staticmethod
    def decode(token: str) -> dict | None:
        """
        Проверяет подлинность и срок действия переданного JWT токена
        """

        try:
            decoded_token = decode(
                token,
                settings.jwt.secret_key,
                algorithms=[settings.jwt.algorithm],
            )

            if decoded_token["exp"] < time.time():
                return None

            user_data = {
                "user_id": decoded_token.get("sub"),
                "roles": decoded_token.get("roles", []),
                "is_superuser": decoded_token.get("is_superuser", False),
                "token": token,
            }

            return UserJWT(**user_data)
        except (ExpiredSignatureError, InvalidTokenError):
            return None