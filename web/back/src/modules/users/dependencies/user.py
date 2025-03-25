from typing import Annotated

from fastapi import Depends

from src.core.schemas import BasePaginationParams
from src.core.dependencies import get_pagination_params
from src.modules.users.dependencies.uow import get_unit_of_work
from src.modules.users.schemas.user import UserQueryParams
from src.modules.users.serializers.user import UserSerializer
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.services.user import UserService


def get_user_params(
        pagination: Annotated[BasePaginationParams, Depends(get_pagination_params)],
) -> UserQueryParams:
    """ Получает query-параметры фильтрации для пользователей """

    return UserQueryParams(
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_user_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
):
    serializer = UserSerializer()
    return UserService(uow, serializer=serializer)