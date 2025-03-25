from typing import List, Union, Annotated
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis

from src.db.redis import get_redis
from src.modules.users.dependencies.uow import get_unit_of_work
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.services.auth import AuthService
from src.exceptions.base import BaseException
from src.core.schemas import UserJWT
from src.utils.token import JWTHelper

http_bearer = HTTPBearer()


async def get_auth_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
        redis: Annotated[Redis, Depends(get_redis)],
):
    jwt_helper = JWTHelper()
    return AuthService(uow, redis, jwt_helper)