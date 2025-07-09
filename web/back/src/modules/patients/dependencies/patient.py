from typing import Annotated
from fastapi import Depends, Query

from src.core.schemas import BasePaginationParams
from src.core.dependencies import get_pagination_params
from src.modules.patients.dependencies.uow import get_unit_of_work
from src.modules.patients.schemas.patient import PatientQueryParams
from src.modules.patients.repositories.uow import UnitOfWork
from src.modules.patients.services.patient import PatientService


def get_patient_params(
        pagination: Annotated[BasePaginationParams, Depends(get_pagination_params)],
        organization_id: str | None = Query(None, description='Параметр фильтрации по id организации'),
) -> PatientQueryParams:
    """ Получает query-параметры фильтрации для пациентов """

    return PatientQueryParams(
        limit=pagination.limit,
        offset=pagination.offset,
        organization_id=organization_id,
    )


def get_patient_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> PatientService:
    """
    Возвращает экземпляр PatientService с переданным UnitOfWork (UoW)
    """
    return PatientService(uow=uow)