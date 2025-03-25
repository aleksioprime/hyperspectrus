"""
Модуль содержит сервисы для аутентификации и регистрации пользователей
"""

from uuid import UUID
from typing import List

from redis.asyncio import Redis

from src.core.config import settings
from src.exceptions.base import BaseException
from src.models.user import User
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.schemas.auth import AuthSchema
from src.modules.users.schemas.token import TokenSchema, AccessTokenSchema
from src.utils.token import JWTHelper


class AuthService:
    """
    Сервис для управления аутентификацией, обновлением токена и выходом пользователей
    """

    def __init__(self, uow: UnitOfWork, redis: Redis, jwt_helper: JWTHelper):
        """
        Инициализирует AuthService с UnitOfWork и Redis
        """
        self.uow = uow
        self.redis = redis
        self.jwt_helper = jwt_helper

    async def login(self, body: AuthSchema) -> TokenSchema:
        """
        Аутентифицирует пользователя и генерирует JWT токены
        """
        async with self.uow:
            user = await self._login(body)
            roles = await self._get_user_roles(user.id)
            tokens = await self._generate_jwt_tokens(user.id, roles)

        return tokens

    async def refresh(self, refresh_token: str):
        """
        Обновляет access-токен
        """
        await self._is_token_valid(refresh_token)
        new_tokens = self.jwt_helper.refresh_access_token(refresh_token)

        return AccessTokenSchema(
            access_token=new_tokens,
        )

    async def logout(self, tokens: TokenSchema):
        """
        Выполняет выход из аккаунта: помечает refresh_token отозванным
        """
        await self._is_token_valid(tokens.refresh_token)
        await self._revoke_token(tokens.refresh_token, settings.jwt.refresh_token_expire_time)

    async def _login(self, body: AuthSchema) -> User:
        """
        Аутентифицирует пользователя
        """
        user: User = await self.uow.auth.get_user_by_username(body.username)
        if not user or not user.check_password(body.password):
            raise BaseException('Ошибка имени пользователя или пароля')

        return user

    async def _get_user_roles(self, user_id: str) -> List[str]:
        """
        Получает список ролей пользователя
        """
        roles = await self.uow.auth.get_roles_by_user(user_id)

        return roles

    async def _generate_jwt_tokens(self, user_id: str | UUID, roles: list) -> TokenSchema:
        """
        Генерирует пару jwt токенов
        """
        access_token, refresh_token = self.jwt_helper.generate_token_pair(user_id, roles)
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def _is_token_valid(self, token: str) -> None:
        """
        Валидирует токен
        """
        is_revoked = await self.redis.get(name=token)
        if is_revoked and is_revoked.decode() == "revoked":
            raise BaseException("Token has been revoked")

    async def _revoke_token(self, token: str, expire_time: int):
        """
        Сохраняет отозванный токен в Redis
        """
        await self.redis.set(
            name=token,
            value="revoked",
            ex=expire_time,
        )
