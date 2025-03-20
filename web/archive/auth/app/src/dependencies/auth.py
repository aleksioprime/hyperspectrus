from typing import List, Union, Annotated
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis

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
        raise TokenValidationError("Токен невалидный")

    try:
        payload = JWTHelper().verify(token)
    except JWTError as e:
        raise JWTError(e.message)

    return UserJWT(
        id=payload['sub'],
        roles=payload['roles'],
    )


def get_user_with_check_roles(required_roles: List[Union[str, Enum]]):

    role_values = [role.value if isinstance(role, Enum) else role for role in required_roles]

    async def role_checker(
            user: Annotated[UserJWT, Depends(get_user_by_jwt)],
            ):
        if not any(role in user.roles for role in role_values):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции"
            )
        return user
    return role_checker