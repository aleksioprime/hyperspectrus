from typing import Annotated
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import BasePaginationParams
from src.core.dependencies import get_pagination_params
from src.db.postgres import get_db_session
from src.modules.patients.services.patient import PatientService
from src.modules.patients.repositories.patient import PatientRepository
from src.modules.patients.schemas.patient import PatientQueryParams



def get_patient_params(
        pagination: Annotated[BasePaginationParams, Depends(get_pagination_params)],
        organization: str | None = Query(None, description='Параметр фильтрации по id организации'),
) -> PatientQueryParams:
    """ Получает query-параметры фильтрации для пациентов """

    return PatientQueryParams(
        limit=pagination.limit,
        offset=pagination.offset,
        organization=organization,
    )


async def get_patient_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PatientRepository:
    """
    Получает экземпляр PatientRepository с переданным AsyncSession (асинхронная сессия базы данных)
    """
    return PatientRepository(session)


def get_patient_service(
    repository: Annotated[PatientRepository, Depends(get_patient_repository)],
) -> PatientService:
    """
    Возвращает экземпляр PatientService с репозиторием
    """
    return PatientService(repository=repository)