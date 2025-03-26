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
from src.modules.parameters.dependencies.spectrum import get_spectrum_service, get_spectrum_params
from src.modules.parameters.schemas.spectrum import SpectrumSchema, SpectrumCreateSchema, SpectrumUpdateSchema, SpectrumQueryParams
from src.modules.parameters.services.spectrum import SpectrumService


router = APIRouter()

@router.get(
    path='/',
    summary='Получить все спектры',
    response_model=list[SpectrumSchema],
    status_code=status.HTTP_200_OK,
)
async def get_spectrums(
        params: Annotated[SpectrumQueryParams, Depends(get_spectrum_params)],
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> list[SpectrumSchema]:
    """
    Возвращает список всех спектров
    """
    spectrums = await service.get_all(params)
    return spectrums


@router.post(
    path='/',
    summary='Создать спектр',
    status_code=status.HTTP_201_CREATED,
)
async def create_spectrum(
        body: SpectrumCreateSchema,
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> SpectrumSchema:
    """
    Создаёт новый спектр
    """
    spectrum = await service.create(body)
    return spectrum


@router.patch(
    path='/{spectrum_id}',
    summary='Обновить спектр',
    response_model=SpectrumSchema,
    status_code=status.HTTP_200_OK,
)
async def update_spectrum(
        spectrum_id: UUID,
        body: SpectrumUpdateSchema,
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> SpectrumSchema:
    """
    Обновляет спектр по его ID
    """
    spectrum = await service.update(spectrum_id, body)
    return spectrum


@router.delete(
    path='/{spectrum_id}',
    summary='Удалить спектр',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_spectrum(
        spectrum_id: UUID,
        service: Annotated[SpectrumService, Depends(get_spectrum_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> None:
    """
    Удаляет спектр по его ID
    """
    await service.delete(spectrum_id)