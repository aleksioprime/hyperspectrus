"""
Модуль с эндпоинтами для управления хромофорами
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.parameters.dependencies.chromophore import get_chromophore_service
from src.modules.parameters.schemas.chromophore import ChromophoreSchema, ChromophoreUpdateSchema
from src.modules.parameters.services.chromophore import ChromophoreService


router = APIRouter()

@router.get(
    path='/',
    summary='Получить все хромофоры',
    response_model=list[ChromophoreSchema],
    status_code=status.HTTP_200_OK,
)
async def get_chromophores(
        service: Annotated[ChromophoreService, Depends(get_chromophore_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE, RoleName.ADMIN}))],
) -> list[ChromophoreSchema]:
    """
    Возвращает список всех хромофоров
    """
    chromophores = await service.get_all()
    return chromophores


@router.post(
    path='/',
    summary='Создать хромофор',
    status_code=status.HTTP_201_CREATED,
)
async def create_chromophore(
        body: ChromophoreUpdateSchema,
        service: Annotated[ChromophoreService, Depends(get_chromophore_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> ChromophoreSchema:
    """
    Создаёт новый хромофор
    """
    chromophore = await service.create(body)
    return chromophore


@router.patch(
    path='/{chromophore_id}/',
    summary='Обновить спектр',
    response_model=ChromophoreSchema,
    status_code=status.HTTP_200_OK,
)
async def update_chromophore(
        chromophore_id: UUID,
        body: ChromophoreUpdateSchema,
        service: Annotated[ChromophoreService, Depends(get_chromophore_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> ChromophoreSchema:
    """
    Обновляет хромофор по его ID
    """
    chromophore = await service.update(chromophore_id, body)
    return chromophore


@router.delete(
    path='/{chromophore_id}/',
    summary='Удалить хромофор',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chromophore(
        chromophore_id: UUID,
        service: Annotated[ChromophoreService, Depends(get_chromophore_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> None:
    """
    Удаляет хромофор по его ID
    """
    await service.delete(chromophore_id)