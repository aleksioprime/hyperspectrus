from uuid import UUID
from typing import Generic, TypeVar, List

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="Список элементов на текущей странице")
    total: int = Field(..., description="Общее количество элементов")
    limit: int = Field(..., description="Максимальное количество элементов на странице")
    offset: int = Field(..., description="Смещение от начала коллекции")
    has_next: bool = Field(..., description="Есть ли следующая страница")
    has_previous: bool = Field(..., description="Есть ли предыдущая страница")


class BasePaginationParams(BaseModel):
    """ Базовый класс параметров пагинации """
    limit: int = Field(Query(alias='limit', gt=0))
    offset: int = Field(Query(alias='offset', ge=0))


class UserJWT(BaseModel):
    """
    Схема для представления данных пользователя в JWT
    """
    user_id: UUID = Field(..., description="Уникальный идентификатор пользователя")
    roles: list = Field(..., description="Список ролей пользователя")
    is_superuser: bool = Field(False, description="Суперпользователь")