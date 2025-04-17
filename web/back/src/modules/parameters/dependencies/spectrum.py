from typing import Annotated
from fastapi import Depends, Query

from src.modules.parameters.dependencies.uow import get_unit_of_work
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.services.spectrum import SpectrumService


def get_spectrum_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> SpectrumService:
    """
    Возвращает экземпляр SpectrumService с переданным UnitOfWork (UoW)
    """
    return SpectrumService(uow=uow)