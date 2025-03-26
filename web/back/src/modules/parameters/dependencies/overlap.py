from typing import Annotated

from fastapi import Depends

from src.modules.parameters.dependencies.uow import get_unit_of_work
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.services.overlap import OverlapCoefficientService


async def get_overlap_coefficient_service(
        uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
):
    return OverlapCoefficientService(uow=uow)