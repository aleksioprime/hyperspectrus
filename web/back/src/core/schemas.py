from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, Field


class BasePaginationParams(BaseModel):
    """ Базовый класс параметров пагинации """
    limit: int = Field(Query(alias='page_size', gt=0))
    offset: int = Field(Query(alias='page_number', ge=0))


class UserJWT(BaseModel):
    """
    Схема для представления данных пользователя в JWT
    """
    user_id: UUID = Field(..., description="Уникальный идентификатор пользователя")
    roles: list = Field(..., description="Список ролей пользователя")