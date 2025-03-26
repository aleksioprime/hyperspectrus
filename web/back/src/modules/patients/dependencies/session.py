from typing import Annotated
from fastapi import Depends, Query

from src.core.schemas import BasePaginationParams
from src.core.dependencies import get_pagination_params
from src.modules.patients.dependencies.uow import get_unit_of_work
from src.modules.patients.schemas.session import SessionQueryParams
from src.modules.patients.repositories.uow import UnitOfWork
from src.modules.patients.services.session import SessionService


def get_session_params(
        pagination: Annotated[BasePaginationParams, Depends(get_pagination_params)],
        patient: str | None = Query(None, description='Параметр фильтрации по ID пациента'),
) -> SessionQueryParams:
    """ Получает query-параметры фильтрации для пациентов """

    return SessionQueryParams(
        limit=pagination.limit,
        offset=pagination.offset,
        patient=patient,
    )


def get_session_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> SessionService:
    """
    Возвращает экземпляр SessionService с переданным UnitOfWork (UoW)
    """
    return SessionService(uow=uow)