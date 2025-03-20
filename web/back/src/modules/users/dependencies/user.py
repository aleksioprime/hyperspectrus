from typing import Annotated

from fastapi import Depends

from src.modules.users.dependencies.uow import get_unit_of_work
from src.modules.users.serializers.user import UserSerializer
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.services.user import UserService


async def get_user_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
):
    serializer = UserSerializer()
    return UserService(uow, serializer=serializer)