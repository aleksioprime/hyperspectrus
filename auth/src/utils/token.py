import jwt
from datetime import timedelta
from uuid import UUID

from src.core.config import settings
from src.exceptions.auth import TokenValidationError
from src.utils.time import get_current_utc_time


class JWTHelper:
    """
    Класс для работы с JWT токенами
    """

    @staticmethod
    def create_token(user_id: str, roles: list[str], expiration: timedelta) -> str:
        """
        Создает JWT токен
        """
        now = get_current_utc_time()
        payload = {
            'sub': user_id,             # Идентификатор пользователя
            'iat': now,                 # Время создания токена
            'exp': now + expiration,    # Время истечения токена
            'roles': roles,               # Роли пользователя
        }

        encoded_jwt = jwt.encode(payload, key=settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
        return encoded_jwt

    def generate_token_pair(self, user_id: str | UUID, roles: list[str]) -> tuple[str, str]:
        """
        Генерирует пару access и refresh токенов
        """
        if isinstance(user_id, UUID):
            user_id = str(user_id)

        access_token = self.create_token(
            user_id=user_id,
            roles=roles,
            expiration=settings.jwt.access_token_expire_time,
        )
        refresh_token = self.create_token(
            user_id=user_id,
            roles=roles,
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
            raise TokenValidationError('Token has expired')
        except jwt.InvalidTokenError:
            raise TokenValidationError('Invalid token')

        return payload

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Обновляет access токен с использованием действующего refresh токена
        """
        payload = self.verify(refresh_token)

        user_id = payload['sub']
        roles = payload.get('roles', [])
        new_access_token = self.create_token(
            user_id=user_id,
            roles=roles,
            expiration=settings.jwt.access_token_expire_time,
        )

        return new_access_token
