"""
Модуль с эндпоинтами для управления ролями пользователей
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.dependencies.auth import get_user_by_jwt, get_user_with_check_roles
from src.dependencies.role import get_role_service
from src.schemas.user import UserJWT
from src.schemas.role import RoleUpdateSchema, RoleSchema
from src.services.role import RoleService
from src.constants.role import RoleName

router = APIRouter()

@router.get(
    path='/roles',
    summary='Получить все роли пользователей',
    response_model=list[RoleSchema],
    status_code=status.HTTP_200_OK,
)
async def get_role_all(
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(get_user_with_check_roles([RoleName.ADMIN]))],
) -> list[RoleSchema]:
    """
    Возвращает список всех ролей
    """
    roles = await service.get_role_all()
    return roles


@router.post(
    path='/roles',
    summary='Создаёт роль',
    description='Создаёт роль, если пользователь авторизован',
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(get_user_with_check_roles([RoleName.ADMIN]))],
        body: RoleUpdateSchema,
) -> RoleSchema:
    """
    Создаёт новую роль
    """
    role = await service.create(body)
    return role


@router.patch(
    path='/roles/{role_id}',
    summary='Обновляет роль',
    description='Обновляет данные существующей роли',
    response_model=RoleSchema,
    status_code=status.HTTP_200_OK,
)
async def update_role(
        role_id: UUID,
        body: RoleUpdateSchema,
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(get_user_with_check_roles([RoleName.ADMIN]))],
) -> RoleSchema:
    """
    Обновляет роль
    """
    role = await service.update(role_id, body)
    return role


@router.delete(
    path='/roles/{role_id}',
    summary='Удаляет роль',
    description='Удаляет роль по заданному идентификатору',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
        role_id: UUID,
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(get_user_with_check_roles([RoleName.ADMIN]))],
) -> None:
    """
    Удаляет роль
    """
    await service.delete(role_id)