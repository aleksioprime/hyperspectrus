from typing import Annotated
from fastapi import Depends, Query

from src.modules.patients.dependencies.uow import get_unit_of_work
from src.modules.patients.repositories.uow import UnitOfWork
from src.modules.patients.services.result import ResultService


def get_result_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> ResultService:
    """
    Возвращает экземпляр ResultService с переданным UnitOfWork (UoW)
    """
    return ResultService(uow=uow)