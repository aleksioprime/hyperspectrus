from pydantic import BaseModel, Field
from uuid import UUID
from typing import List


class UserJWT(BaseModel):
    """
    Схема для представления данных пользователя в JWT
    """
    user_id: UUID = Field(..., description="Уникальный идентификатор пользователя")
    roles: list = Field(..., description="Список ролей пользователя")
    token: str = Field(..., description="Токен")


class UserSchema(BaseModel):
    """
    Схема пользователя, полученного через сервис авторизации
    """
    user_id: UUID = Field(..., description="ID пользователя")
    email: str = Field(..., description="Email пользователя")
    roles: List[str] = Field(..., description="Роли пользователя")