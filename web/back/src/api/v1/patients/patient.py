"""
Модуль с эндпоинтами для управления пациентами
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT, PaginatedResponse
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.patients.dependencies.patient import get_patient_service, get_patient_params
from src.modules.patients.schemas.patient import PatientSchema, PatientCreateSchema, PatientUpdateSchema, PatientDetailSchema, PatientQueryParams
from src.modules.patients.services.patient import PatientService
from src.modules.users.services.user import UserService
from src.modules.users.dependencies.user import get_user_service


router = APIRouter()

@router.get(
    path='/',
    summary='Получить всех пациентов',
    response_model=PaginatedResponse[PatientSchema],
    status_code=status.HTTP_200_OK,
)
async def get_patients(
        params: Annotated[PatientQueryParams, Depends(get_patient_params)],
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE, RoleName.ADMIN}))],
        user_service: Annotated[UserService, Depends(get_user_service)],
) -> PaginatedResponse[PatientSchema]:
    """
    Возвращает список всех пациентов организации
    """
    user_obj = await user_service.get_user_by_id(user.user_id)

    patients = await service.get_all(params, user_obj)
    return patients


@router.get(
    path='/{patient_id}/',
    summary='Получить детальную информацию о пациенте',
    response_model=PatientDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_patient(
        patient_id: UUID,
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> PatientDetailSchema:
    """
    Получает детальную информацию о пациенте
    """
    patient = await service.get_by_id(patient_id)
    return patient


@router.post(
    path='/',
    summary='Создаёт пациента',
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
        body: PatientCreateSchema,
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> PatientSchema:
    """
    Создаёт нового пациента
    """
    patient = await service.create(body)
    return patient


@router.patch(
    path='/{patient_id}/',
    summary='Обновляет пациента',
    response_model=PatientSchema,
    status_code=status.HTTP_200_OK,
)
async def update_patient(
        patient_id: UUID,
        body: PatientUpdateSchema,
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> PatientSchema:
    """
    Обновляет пациента по его ID
    """
    patient = await service.update(patient_id, body)
    return patient


@router.delete(
    path='/{patient_id}/',
    summary='Удаляет пациента',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_patient(
        patient_id: UUID,
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет пациента по его ID
    """
    await service.delete(patient_id)