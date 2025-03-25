"""
Модуль с эндпоинтами API для аутентификации и управления сессиями пользователей
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.modules.users.dependencies.auth import get_auth_service
from src.modules.users.schemas.auth import AuthSchema
from src.modules.users.schemas.token import TokenSchema, RefreshTokenSchema, AccessTokenSchema
from src.modules.users.services.auth import AuthService


router = APIRouter()


@router.post(
    path='/login',
    summary='Выполняет вход в аккаунт',
    description='Авторизирует пользователя, выдает новые jwt токены',
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
)
async def login(
        body: AuthSchema,
        service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenSchema:
    """
    Авторизует пользователя и выдает новые jwt токены
    """
    token_pair: TokenSchema = await service.login(body)
    return token_pair


@router.post(
    path='/logout',
    summary='Выполняет выход из аккаунта',
    description='Помечает access токен отозванным, а refresh токен удаляет из базы',
    status_code=status.HTTP_200_OK,
)
async def logout(
        tokens: TokenSchema,
        service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Выполняет выход из аккаунта пользователя, отзывает токены
    """

    await service.logout(tokens)


@router.post(
    path='/refresh',
    summary='Выдает новый access-токен',
    description='Выдает новый access-токен по предоставленному refresh-токену',
    response_model=AccessTokenSchema,
    status_code=status.HTTP_200_OK,
)
async def refresh_tokens(
        token: RefreshTokenSchema,
        service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessTokenSchema:
    """
    Выдает новый access-токен по предоставленному refresh-токену
    """

    token_pair = await service.refresh(token.refresh_token)
    return token_pair