"""
Модуль с эндпоинтами API для аутентификации и управления сессиями пользователей
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.dependencies.auth import get_auth_service
from src.schemas.auth import RegisterSchema, AuthSchema
from src.schemas.token import TokenSchema, RefreshTokenSchema, AccessTokenSchema
from src.services.auth import AuthService

router = APIRouter()


@router.post(
    path='/register',
    summary='Регистрирует пользователя',
    description='Регистрирует пользователя, выдает jwt токены и сохраняет refresh токен в базу',
    status_code=status.HTTP_201_CREATED,
    response_model=TokenSchema,
)
async def register(
        body: RegisterSchema,
        service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenSchema:
    """
    Регистрирует нового пользователя, выдает токены и сохраняет refresh токен в базу данных
    """
    user: TokenSchema = await service.register(body)
    return user


@router.post(
    path='/auth',
    summary='Авторизирует пользователя',
    description='Авторизирует пользователя, выдает новые jwt токены и записывает вход в историю',
    response_model=TokenSchema,
)
async def authenticate(
        body: AuthSchema,
        service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenSchema:
    """
    Авторизует пользователя и выдает новые jwt токены
    """
    token_pair: TokenSchema = await service.auth(body)
    return token_pair


@router.post(
    path='/logout',
    summary='Выполняет выход из аккаунта',
    description='Помечает access токен отозванным, а refresh токен удаляет из базы',
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