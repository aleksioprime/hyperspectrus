from typing import Annotated

from fastapi import Depends

from src.modules.parameters.dependencies.uow import get_unit_of_work
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.services.device import DeviceService


async def get_device_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
):
    return DeviceService(uow=uow)