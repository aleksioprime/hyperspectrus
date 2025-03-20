"""
Модуль с эндпоинтами для управления пациентами
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.constants.role import RoleName
from src.dependencies.auth import JWTBearer
from src.dependencies.patient import get_patient_service, get_patient_params
from src.schemas.auth import UserJWT
from src.schemas.patient import PatientSchema, PatientCreateSchema, PatientUpdateSchema, PatientDetailSchema, PatientQueryParams
from src.services.patient import PatientService


router = APIRouter()

@router.get(
    path='/patients',
    summary='Получить всех пациентов',
    response_model=list[PatientSchema],
    status_code=status.HTTP_200_OK,
)
async def get_patients(
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
        params: Annotated[PatientQueryParams, Depends(get_patient_params)],
) -> list[PatientSchema]:
    """
    Возвращает список всех пациентов организации
    """
    patients = await service.get_all(params)
    return patients


@router.get(
    path='/patients/{patient_id}',
    summary='Получить детальную информацию о пациенте',
    description='Получает детальную информацию о пациенте',
    response_model=PatientDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_patient(
        patient_id: UUID,
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> PatientDetailSchema:
    """
    Получает детальную информацию о пациенте
    """
    patient = await service.get_by_id(patient_id)
    return patient


@router.post(
    path='/patients',
    summary='Создаёт пациента',
    description='Создаёт нового пациента',
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
        body: PatientCreateSchema,
) -> PatientSchema:
    """
    Создаёт нового пациента
    """
    patient = await service.create(body)
    return patient


@router.patch(
    path='/patients/{patient_id}',
    summary='Обновляет пациента',
    description='Обновляет данные существующего пациента',
    response_model=PatientSchema,
    status_code=status.HTTP_200_OK,
)
async def update_patient(
        patient_id: UUID,
        body: PatientUpdateSchema,
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> PatientSchema:
    """
    Обновляет пациента
    """
    patient = await service.update(patient_id, body)
    return patient


@router.delete(
    path='/patients/{patient_id}',
    summary='Удаляет пациента',
    description='Удаляет пациента по заданному идентификатору',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_patient(
        patient_id: UUID,
        service: Annotated[PatientService, Depends(get_patient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> None:
    """
    Удаляет пациента
    """
    await service.delete(patient_id)