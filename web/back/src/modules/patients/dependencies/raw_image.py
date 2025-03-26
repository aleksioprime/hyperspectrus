from typing import Annotated
from fastapi import Depends, Query

from src.core.schemas import BasePaginationParams
from src.core.dependencies import get_pagination_params
from src.modules.patients.dependencies.uow import get_unit_of_work
from src.modules.patients.schemas.raw_image import RawImageQueryParams
from src.modules.patients.repositories.uow import UnitOfWork
from src.modules.patients.services.raw_image import RawImageService


def get_raw_image_params(
        pagination: Annotated[BasePaginationParams, Depends(get_pagination_params)],
        session: str | None = Query(None, description='Параметр фильтрации по ID пациента'),
) -> RawImageQueryParams:
    """ Получает query-параметры фильтрации для исходных изображений """

    return RawImageQueryParams(
        limit=pagination.limit,
        offset=pagination.offset,
        session=session,
    )


def get_raw_image_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> RawImageService:
    """
    Возвращает экземпляр RawImageService с переданным UnitOfWork (UoW)
    """
    return RawImageService(uow=uow)