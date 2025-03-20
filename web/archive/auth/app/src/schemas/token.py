from uuid import UUID
from pydantic import BaseModel, Field


class TokenSchema(BaseModel):
    """
    Схема для передачи пары токенов (access и refresh)
    """

    access_token: str = Field(..., description="Access-токен для доступа к ресурсам")
    refresh_token: str = Field(..., description="Refresh-токен для обновления access-токена")


class RefreshTokenSchema(BaseModel):
    """
    Схема для передачи refresh-токена.
    Используется для обновления access-токена
    """

    refresh_token: str = Field(..., description="Refresh-токен для обновления access-токена")


class AccessTokenSchema(BaseModel):
    """
    Схема для возвращения access-токена при обновлении
    """

    access_token: str = Field(..., description="Access-токен для доступа к защищенным ресурсам")
