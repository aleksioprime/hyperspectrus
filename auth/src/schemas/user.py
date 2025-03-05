from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class UserJWT(BaseModel):
    """
    Схема для представления данных пользователя в JWT
    """
    id: UUID = Field(..., description="Уникальный идентификатор пользователя")
    roles: list = Field(..., description="Список ролей пользователя")


class RoleSchema(BaseModel):
    """
    Схема для представления данных о роли
    """
    id: UUID = Field(..., description="Уникальный идентификатор роли")
    name: str = Field(..., description="Название роли")
    description: str = Field(..., description="Описание роли")

    class Config:
        """
        Дополнительная конфигурация для поддержки from_orm
        """
        from_attributes = True


class UserSchema(BaseModel):
    """
    Схема для представления данных пользователя
    """
    id: UUID = Field(..., description="Уникальный идентификатор пользователя")
    first_name: Optional[str] = Field(None, description="Имя пользователя")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя")
    login: Optional[str] = Field(None, description="Логин пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    roles: List[RoleSchema] = Field(..., description="Список ролей пользователя")


class UserUpdate(BaseModel):
    """
    Схема для обновления данных пользователя
    """
    login: Optional[str] = Field(None, description="Логин пользователя для обновления")
    first_name: Optional[str] = Field(None, description="Имя пользователя для обновления")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя для обновления")
    email: Optional[str] = Field(None, description="Email пользователя")
