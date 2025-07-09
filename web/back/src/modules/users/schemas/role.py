from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class RoleSchema(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор роли")
    name: str = Field(..., description="Название роли")
    description: str | None = Field(None, description="Описание роли")
    display_name: str | None = Field(None, description="Отображение названия")

    class Config:
        from_attributes = True


class RoleUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Название роли")
    description: Optional[str] = Field(None, description="Описание роли")
    display_name: str | None = Field(None, description="Отображение названия")


class RoleAssignment(BaseModel):
    role_id: UUID = Field(..., description="Уникальный идентификатор роли")