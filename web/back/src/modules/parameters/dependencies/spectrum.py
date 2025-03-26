from typing import Annotated
from fastapi import Depends, Query

from src.core.schemas import BasePaginationParams
from src.core.dependencies import get_pagination_params
from src.modules.parameters.dependencies.uow import get_unit_of_work
from src.modules.parameters.schemas.spectrum import SpectrumQueryParams
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.services.spectrum import SpectrumService


def get_spectrum_params(
        pagination: Annotated[BasePaginationParams, Depends(get_pagination_params)],
        device: str | None = Query(None, description='Параметр фильтрации по ID устройства'),
) -> SpectrumQueryParams:
    """ Получает query-параметры фильтрации для спектров """

    return SpectrumQueryParams(
        limit=pagination.limit,
        offset=pagination.offset,
        device=device,
    )


def get_spectrum_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> SpectrumService:
    """
    Возвращает экземпляр SpectrumService с переданным UnitOfWork (UoW)
    """
    return SpectrumService(uow=uow)