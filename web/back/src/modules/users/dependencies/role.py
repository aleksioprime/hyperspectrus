from typing import Annotated

from fastapi import Depends

from src.modules.users.dependencies.uow import get_unit_of_work
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.services.role import RoleService



async def get_role_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
):
    return RoleService(uow=uow)