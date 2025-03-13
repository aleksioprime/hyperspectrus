"""
Модуль с эндпоинтами для управления пользователями
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.dependencies.auth import get_user_by_jwt, check_roles
from src.dependencies.user import get_user_service
from src.schemas.user import UserUpdateSchema, UserJWT, UserSchema
from src.schemas.role import RoleAssignment
from src.services.user import UserService
from src.constants.role import RoleName

router = APIRouter()

@router.get(
    path='/users',
    summary='Получить всех пользователей',
    response_model=list[UserSchema],
    status_code=status.HTTP_200_OK,
)
@check_roles([RoleName.ADMIN])
async def get_all_users(
        service: Annotated[UserService, Depends(get_user_service)],
        user: Annotated[UserJWT, Depends(get_user_by_jwt)],
) -> list[UserSchema]:
    """
    Возвращает список всех пользователей
    """
    users = await service.get_user_all()
    return users

@router.get(
    path='/users/me',
    summary='Получить информацию о себе',
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def get_user_me(
    user_jwt: Annotated[UserJWT, Depends(get_user_by_jwt)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Возвращает информацию о текущем пользователе
    """
    user = await service.get_user_by_id(user_jwt.id)
    return user

@router.patch(
    path='/users/{user_id}',
    summary='Обновление пользователя',
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
@check_roles([RoleName.ADMIN])
async def update_user(
    user_id: UUID,
    user: Annotated[UserJWT, Depends(get_user_by_jwt)],
    body: UserUpdateSchema,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Обновляет информацию о пользователе
    """
    user = await service.update(user_id, body=body)
    return user

@router.delete(
    path='/users/{user_id}',
    summary='Удаление пользователя',
    status_code=status.HTTP_204_NO_CONTENT,
)
@check_roles([RoleName.ADMIN])
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    user: Annotated[UserJWT, Depends(get_user_by_jwt)],
):
    """
    Удаляет пользователя
    """
    await service.delete(user_id)


@router.post(
    path='/users/{user_id}/role/add',
    summary='Назначить роль пользователю',
    status_code=status.HTTP_200_OK,
)
@check_roles([RoleName.ADMIN])
async def add_role_to_user(
        user_id: UUID,
        role_assignment: RoleAssignment,
        service: Annotated[UserService, Depends(get_user_service)],
        user: Annotated[UserJWT, Depends(get_user_by_jwt)],
):
    """
    Назначает роль пользователю
    """
    await service.role_add(user_id, role_assignment.role_id)


@router.post(
    path='/users/{user_id}/role/remove',
    summary='Отозвать роль у пользователя',
    status_code=status.HTTP_200_OK,
)
@check_roles([RoleName.ADMIN])
async def remove_role_from_user(
        user_id: UUID,
        role_assignment: RoleAssignment,
        service: Annotated[UserService, Depends(get_user_service)],
        user: Annotated[UserJWT, Depends(get_user_by_jwt)],
):
    """
    Отзывает роль у пользователя
    """
    await service.role_remove(user_id, role_assignment.role_id)