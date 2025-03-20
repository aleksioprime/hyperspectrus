"""
Модуль содержит сервисы для аутентификации и регистрации пользователей
"""

from uuid import UUID
from typing import List

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from src.core.config import settings
from src.exceptions.auth import RegisterError, LoginError, TokenValidationError
from src.repositories.uow import UnitOfWork
from src.models.user import User
from src.schemas.auth import RegisterSchema, AuthSchema
from src.schemas.token import TokenSchema, AccessTokenSchema
from src.utils.token import JWTHelper


class AuthService:
    """
    Сервис для управления аутентификацией, регистрацией и выходом пользователей
    """

    def __init__(self, uow: UnitOfWork, redis: Redis):
        """
        Инициализирует AuthService с UnitOfWork и Redis
        """
        self.uow = uow
        self.redis = redis
        self.jwt_helper = JWTHelper()

    async def register(self, body: RegisterSchema) -> TokenSchema:
        """
        Регистрирует нового пользователя, генерирует для него JWT токены и отправляет уведомление
        """
        async with self.uow:
            user: User = await self._register(body)
            roles: list[str] = await self._get_user_roles(user.id)
            tokens: TokenSchema = await self._generate_jwt_tokens(user.id, roles)

        return tokens

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
        await self._revoke_refresh_token(tokens.refresh_token)

    async def _register(self, body: RegisterSchema) -> User:
        """
        Регистрирует пользователя
        """
        try:
            user = await self.uow.auth.register(body)
        except IntegrityError as exc:
            raise RegisterError(message='User already exists!') from exc

        return user

    async def _get_user_roles(self, user_id: str) -> List[str]:
        """
        Получает список ролей пользователя
        """
        roles = await self.uow.auth.get_roles(user_id)

        return roles

    async def _generate_jwt_tokens(self, user_id: str | UUID, roles: list) -> TokenSchema:
        """
        Генерирует пару jwt токенов
        """

        at, rt = self.jwt_helper.generate_token_pair(user_id, roles)
        return TokenSchema(
            access_token=at,
            refresh_token=rt,
        )

    async def _login(self, body: AuthSchema) -> User:
        """
        Аутентифицирует пользователя
        """
        user: User = await self.uow.auth.get_user_by_login(body.login)
        if not user or not user.check_password(body.password):
            raise LoginError('Wrong login or password')

        return user

    async def _is_token_valid(self, refresh_token: str) -> None:
        """
        Валидирует refresh-токен
        """
        is_revoked = await self.redis.get(name=refresh_token)
        if is_revoked and is_revoked.decode() == "revoked":
            raise TokenValidationError("Refresh token has been revoked")


    async def _revoke_refresh_token(self, refresh_token: str):
        """
        Сохраняет отозванный refresh-токен в Redis
        """
        await self.redis.set(
            name=refresh_token,
            value="revoked",
            ex=settings.jwt.refresh_token_expire_time,
        )
