from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis

from src.core.config import settings
from src.db.redis import get_redis
from src.dependencies.uow import get_unit_of_work
from src.repositories.uow import UnitOfWork
from src.services.auth import AuthService
from src.exceptions.auth import JWTError, TokenValidationError
from src.schemas.user import UserJWT
from src.utils.token import JWTHelper

http_bearer = HTTPBearer()


async def get_auth_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
        redis: Annotated[Redis, Depends(get_redis)],
):
    return AuthService(uow, redis)

async def get_user_by_jwt(
        redis: Annotated[Redis, Depends(get_redis)],
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> UserJWT:
    """ Получение пользователя по jwt токену """
    token = credentials.credentials

    if await redis.get(name=token):
        raise TokenValidationError("Refresh token has been revoked")

    try:
        payload = JWTHelper().verify(token)
    except JWTError as e:
        raise JWTError(e.message)

    return UserJWT(
        id=payload['sub'],
        roles=payload['roles'],
    )