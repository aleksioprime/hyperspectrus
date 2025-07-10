"""
Модуль с эндпоинтами для управления организациями
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.core.security import JWTBearer
from src.constants.role import RoleName
from src.modules.users.dependencies.organization import get_organization_service
from src.modules.users.schemas.organization import OrganizationUpdateSchema, OrganizationSchema
from src.modules.users.services.organization import OrganizationService

router = APIRouter()

@router.get(
    path='/',
    summary='Получить все организации',
    response_model=list[OrganizationSchema],
    status_code=status.HTTP_200_OK,
)
async def get_organization_all(
        service: Annotated[OrganizationService, Depends(get_organization_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> list[OrganizationSchema]:
    """
    Возвращает список всех организаций
    """
    organizations = await service.get_all()
    return organizations


@router.post(
    path='/',
    summary='Создать организацию',
    response_model=OrganizationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
        body: OrganizationUpdateSchema,
        service: Annotated[OrganizationService, Depends(get_organization_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],

) -> OrganizationSchema:
    """
    Создаёт организацию
    """
    organization = await service.create(body)
    return organization


@router.patch(
    path='/{organization_id}/',
    summary='Обновить организацию',
    response_model=OrganizationSchema,
    status_code=status.HTTP_200_OK,
)
async def update_organization(
        organization_id: UUID,
        body: OrganizationUpdateSchema,
        service: Annotated[OrganizationService, Depends(get_organization_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> OrganizationSchema:
    """
    Обновляет организацию
    """
    organization = await service.update(organization_id, body)
    return organization


@router.delete(
    path='/{organization_id}/',
    summary='Удалить организацию',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_organization(
        organization_id: UUID,
        service: Annotated[OrganizationService, Depends(get_organization_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> None:
    """
    Удаляет организацию
    """
    await service.delete(organization_id)