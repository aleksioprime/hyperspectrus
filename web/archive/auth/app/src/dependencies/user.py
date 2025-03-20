from typing import Annotated

from fastapi import Depends

from src.dependencies.uow import get_unit_of_work
from src.repositories.uow import UnitOfWork
from src.services.user import UserService
from src.serializers.user import UserSerializer


async def get_user_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
):
    serializer = UserSerializer()
    return UserService(uow, serializer=serializer)