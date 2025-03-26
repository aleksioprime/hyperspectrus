from typing import Annotated

from fastapi import Depends

from src.modules.parameters.dependencies.uow import get_unit_of_work
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.services.chromophore import ChromophoreService


async def get_chromophore_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
):
    return ChromophoreService(uow=uow)