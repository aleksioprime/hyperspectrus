from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from src.core.schemas import BasePaginationParams

class UserQueryParams(BasePaginationParams):

    class Config:
        arbitrary_types_allowed = True


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
    username: Optional[str] = Field(None, description="Логин пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    organization_id: Optional[str] = Field(None, description="ID организации")
    roles: List[RoleSchema] = Field(..., description="Список ролей пользователя")


class UserCreateSchema(BaseModel):
    """
    Схема для создание пользователя.
    Определяет поля, необходимые для создания нового пользователя
    """

    username: str = Field(..., description="Логин пользователя")
    password: str = Field(..., description="Пароль пользователя")
    email: str = Field(..., description="Email пользователя")
    first_name: str = Field(..., description="Имя пользователя")
    last_name: str = Field(..., description="Фамилия пользователя")
    organization_id: Optional[str] = Field(None, description="ID организации")


class UserUpdateSchema(BaseModel):
    """
    Схема для обновления данных пользователя
    """
    username: Optional[str] = Field(None, description="Логин пользователя для обновления")
    first_name: Optional[str] = Field(None, description="Имя пользователя для обновления")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя для обновления")
    email: Optional[str] = Field(None, description="Email пользователя")
    organization_id: Optional[str] = Field(None, description="ID организации")
