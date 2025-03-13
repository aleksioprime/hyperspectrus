from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis


from src.dependencies.uow import get_unit_of_work
from src.repositories.uow import UnitOfWork
from src.services.role import RoleService
from src.db.redis import get_redis


async def get_role_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
        redis: Annotated[Redis, Depends(get_redis)],
):
    return RoleService(uow, redis)