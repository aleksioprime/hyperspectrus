"""
Модуль с эндпоинтами для управления пользователями
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.core.security import JWTBearer
from src.constants.role import RoleName
from src.modules.users.dependencies.user import get_user_service, get_user_params
from src.modules.users.schemas.user import UserCreateSchema, UserUpdateSchema, UserSchema, UserQueryParams
from src.modules.users.schemas.role import RoleAssignment
from src.modules.users.services.user import UserService

router = APIRouter()


@router.get(
    path='/',
    summary='Получить всех пользователей',
    response_model=list[UserSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_users(
        params: Annotated[UserQueryParams, Depends(get_user_params)],
        service: Annotated[UserService, Depends(get_user_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> list[UserSchema]:
    """
    Возвращает список всех пользователей
    """
    users = await service.get_user_all(params)
    return users

@router.get(
    path='/me',
    summary='Получить информацию о себе',
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def get_user_me(
    service: Annotated[UserService, Depends(get_user_service)],
    user: Annotated[UserJWT, Depends(JWTBearer())],
):
    """
    Возвращает информацию о текущем пользователе
    """
    user = await service.get_user_by_id(user.user_id)
    return user

@router.post(
    path='/',
    summary='Создаёт пользователя',
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema,
)
async def register(
        body: UserCreateSchema,
        service: Annotated[UserService, Depends(get_user_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
) -> UserSchema:
    """
    Регистрирует нового пользователя.
    Зарегистрировать пользователя может только администратор
    """
    user: UserSchema = await service.create(body)
    return user

@router.patch(
    path='/{user_id}',
    summary='Обновление пользователя',
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: UUID,
    body: UserUpdateSchema,
    service: Annotated[UserService, Depends(get_user_service)],
    user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
):
    """
    Обновляет информацию о пользователе
    """
    user = await service.update(user_id, body=body)
    return user

@router.delete(
    path='/{user_id}',
    summary='Удаление пользователя',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
):
    """
    Удаляет пользователя
    """
    await service.delete(user_id, user.user_id)


@router.post(
    path='/{user_id}/role/add',
    summary='Назначить роль пользователю',
    status_code=status.HTTP_200_OK,
)
async def add_role_to_user(
        user_id: UUID,
        role_assignment: RoleAssignment,
        service: Annotated[UserService, Depends(get_user_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
):
    """
    Назначает роль пользователю
    """
    await service.role_add(user_id, role_assignment.role_id)


@router.post(
    path='/{user_id}/role/remove',
    summary='Отозвать роль у пользователя',
    status_code=status.HTTP_200_OK,
)
async def remove_role_from_user(
        user_id: UUID,
        role_assignment: RoleAssignment,
        service: Annotated[UserService, Depends(get_user_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.ADMIN}))],
):
    """
    Отзывает роль у пользователя
    """
    await service.role_remove(user_id, role_assignment.role_id)