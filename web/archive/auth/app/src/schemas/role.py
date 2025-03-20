from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class RoleSchema(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор роли")
    name: str = Field(..., description="Название роли")
    description: str = Field(..., description="Описание роли")

    class Config:
        from_attributes = True


class RoleUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Название роли")
    description: Optional[str] = Field(None, description="Описание роли")


class RoleAssignment(BaseModel):
    role_id: UUID = Field(..., description="Уникальный идентификатор роли")