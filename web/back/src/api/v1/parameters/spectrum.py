"""
Модуль с эндпоинтами для управления спектрами светодиода
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.parameters.dependencies.spectrum import get_spectrum_service
from src.modules.parameters.schemas.spectrum import SpectrumSchema, SpectrumCreateSchema, SpectrumUpdateSchema
from src.modules.parameters.services.spectrum import SpectrumService


router = APIRouter()

@router.get(
    path='/',
    summary='Получить все спектры',
    response_model=list[SpectrumSchema],
    status_code=status.HTTP_200_OK,
)
async def get_spectrums(
        device_id: UUID,
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> list[SpectrumSchema]:
    """
    Возвращает список всех спектров выбранного устройства

    """
    spectrums = await service.get_all(device_id)
    return spectrums


@router.post(
    path='/',
    summary='Создать спектр',
    status_code=status.HTTP_201_CREATED,
)
async def create_spectrum(
        device_id: UUID,
        body: SpectrumCreateSchema,
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> SpectrumSchema:
    """
    Создаёт новый спектр
    """
    spectrum = await service.create(device_id, body)
    return spectrum


@router.patch(
    path='/{spectrum_id}',
    summary='Обновить спектр',
    response_model=SpectrumSchema,
    status_code=status.HTTP_200_OK,
)
async def update_spectrum(
        device_id: UUID,
        spectrum_id: UUID,
        body: SpectrumUpdateSchema,
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> SpectrumSchema:
    """
    Обновляет спектр по его ID
    """
    spectrum = await service.update(device_id, spectrum_id, body)
    return spectrum


@router.delete(
    path='/{spectrum_id}',
    summary='Удалить спектр',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_spectrum(
        device_id: UUID,
        spectrum_id: UUID,
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет спектр по его ID
    """
    await service.delete(device_id, spectrum_id)