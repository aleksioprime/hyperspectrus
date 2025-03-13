from fastapi import Depends

from src.services.auth import AuthService
from src.schemas.auth import UserSchema, UserJWT


auth_service_remote = AuthService(use_remote_auth=True) # Использует API
auth_service_local = AuthService(use_remote_auth=False) # Проверяет токен локально


async def get_user_from_auth(
    user_data: dict = Depends(auth_service_remote),
) -> UserSchema:
    """
   Dependency для получения текущего пользователя через сервис авторизации (полные данные)
    """
    return UserSchema(**user_data)


async def get_user_from_token(
    user_data: dict = Depends(auth_service_local),
) -> UserJWT:
    """
    Dependency для получения текущего пользователя через локальную проверку JWT (минимальные данные)
    """
    return UserJWT(**user_data)