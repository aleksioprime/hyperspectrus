from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from src.core.schemas import BasePaginationParams

class UserQueryParams(BasePaginationParams):
    organization_id: UUID | None = Field(None, description="ID организации")

    class Config:
        arbitrary_types_allowed = True


class RoleSchema(BaseModel):
    """
    Схема для представления данных о роли
    """
    id: UUID = Field(..., description="Уникальный идентификатор роли")
    name: str = Field(..., description="Название роли")
    description: str = Field(..., description="Описание роли")
    display_name: str | None = Field(None, description="Отображение названия")

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
    organization_id: UUID | None = Field(None, description="ID организации")
    is_superuser: bool | None = Field(False, description="Суперпользователь")
    roles: List[RoleSchema] = Field(..., description="Список ролей пользователя")
    photo: str | None = Field(None, description="Изображение пользователя")

    class Config:
        from_attributes = True


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
    organization_id: UUID | None = Field(None, description="ID организации")
    is_superuser: bool | None = Field(False, description="Суперпользователь")
    roles: List[UUID] | None = Field(None, description="Список id ролей пользователя")


class UserUpdateSchema(BaseModel):
    """
    Схема для обновления данных пользователя
    """
    username: str | None = Field(None, description="Логин пользователя для обновления")
    first_name: str | None = Field(None, description="Имя пользователя для обновления")
    last_name: str | None = Field(None, description="Фамилия пользователя для обновления")
    email: str | None = Field(None, description="Email пользователя")
    organization_id: UUID | None = Field(None, description="ID организации")
    is_superuser: bool | None = Field(False, description="Суперпользователь")
    roles: List[UUID] | None = Field(None, description="Список id ролей пользователя")


class UpdatePasswordUserSchema(BaseModel):
    """
    Схема обновления пароля пользователя
    """
    password: str = Field(..., description="Пароль пользователя")