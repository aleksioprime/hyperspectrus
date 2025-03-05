"""
Модуль с эндпоинтами для управления пользователями и их ролями
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.dependencies.auth import get_user_by_jwt
from src.dependencies.user import get_user_service
from src.schemas.user import UserUpdate, UserJWT, UserSchema
from src.services.user import UserService

router = APIRouter()

@router.get(
    path='/user',
    summary='Получить всех пользователей',
    response_model=list[UserSchema],
)
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
    path='/user/me',
    summary='Получить информацию о себе',
    response_model=UserSchema,
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
    path='/user/{user_id}',
    summary='Обновление пользователя',
    response_model=UserSchema,
)
async def update_user(
    user_id: UUID,
    user: Annotated[UserJWT, Depends(get_user_by_jwt)],
    body: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Обновляет информацию о пользователе
    """
    user = await service.update(user_id, body=body)
    return user

@router.delete(
    path='/user/{user_id}',
    summary='Удаление пользователя',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    user: Annotated[UserJWT, Depends(get_user_by_jwt)],
):
    """
    Удаляет пользователя
    """
    await service.delete(user_id)
    return {"message": "Пользователь успешно удалён"}