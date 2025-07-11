"""
Модуль с эндпоинтами для управления устройствами съёмки
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.parameters.dependencies.device import get_device_service
from src.modules.parameters.schemas.device import DeviceSchema, DeviceCreateSchema, DeviceUpdateSchema, DeviceDetailSchema
from src.modules.parameters.services.device import DeviceService


router = APIRouter()

@router.get(
    path='/',
    summary='Получить все устройства',
    response_model=list[DeviceSchema],
    status_code=status.HTTP_200_OK,
)
async def get_devices(
        service: Annotated[DeviceService, Depends(get_device_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE, RoleName.ADMIN}))],
) -> list[DeviceSchema]:
    """
    Возвращает список всех устройств
    """
    devices = await service.get_all()
    return devices


@router.get(
    path='/{device_id}/',
    summary='Получить детальную информацию об устройстве',
    response_model=DeviceDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_device(
        device_id: UUID,
        service: Annotated[DeviceService, Depends(get_device_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> DeviceDetailSchema:
    """
    Получает детальную информацию об устройстве
    """
    device = await service.get_detail_by_id(device_id)
    return device


@router.post(
    path='/',
    summary='Создаёт устройство',
    status_code=status.HTTP_201_CREATED,
)
async def create_device(
        body: DeviceCreateSchema,
        service: Annotated[DeviceService, Depends(get_device_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> DeviceSchema:
    """
    Создаёт новое устройство
    """
    device = await service.create(body)
    return device


@router.patch(
    path='/{device_id}/',
    summary='Обновляет устройство',
    response_model=DeviceSchema,
    status_code=status.HTTP_200_OK,
)
async def update_device(
        device_id: UUID,
        body: DeviceUpdateSchema,
        service: Annotated[DeviceService, Depends(get_device_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> DeviceSchema:
    """
    Обновляет устройство по его ID
    """
    device = await service.update(device_id, body)
    return device


@router.delete(
    path='/{device_id}/',
    summary='Удаляет устройство',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_device(
        device_id: UUID,
        service: Annotated[DeviceService, Depends(get_device_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> None:
    """
    Удаляет устройство по его ID
    """
    await service.delete(device_id)


@router.post(
    path='/{device_id}/overlaps/random-fill/',
    summary='Заполнить матрицу перекрытий случайными значениями для устройства',
    status_code=status.HTTP_200_OK,
)
async def fill_device_overlaps_random(
    device_id: UUID,
    service: Annotated[DeviceService, Depends(get_device_service)],
    user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
):
    """
    Заполняет матрицу перекрытий случайными коэффициентами для всех спектров устройства
    """
    await service.fill_overlaps_random(device_id)
    return {"status": "ok"}