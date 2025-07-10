"""
Модуль с эндпоинтами для управления ролями пользователей
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.core.security import JWTBearer
from src.constants.role import RoleName
from src.modules.users.dependencies.role import get_role_service
from src.modules.users.schemas.role import RoleUpdateSchema, RoleSchema
from src.modules.users.services.role import RoleService

router = APIRouter()

@router.get(
    path='/',
    summary='Получить все роли пользователей',
    response_model=list[RoleSchema],
    status_code=status.HTTP_200_OK,
)
async def get_role_all(
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> list[RoleSchema]:
    """
    Возвращает список всех ролей
    """
    roles = await service.get_all()
    return roles


@router.post(
    path='/',
    summary='Создать роль',
    response_model=RoleSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
        body: RoleUpdateSchema,
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],

) -> RoleSchema:
    """
    Создаёт новую роль
    """
    role = await service.create(body)
    return role


@router.patch(
    path='/{role_id}/',
    summary='Обновить роль',
    response_model=RoleSchema,
    status_code=status.HTTP_200_OK,
)
async def update_role(
        role_id: UUID,
        body: RoleUpdateSchema,
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> RoleSchema:
    """
    Обновляет роль
    """
    role = await service.update(role_id, body)
    return role


@router.delete(
    path='/{role_id}/',
    summary='Удалить роль',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
        role_id: UUID,
        service: Annotated[RoleService, Depends(get_role_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> None:
    """
    Удаляет роль
    """
    await service.delete(role_id)