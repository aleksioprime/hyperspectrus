from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationSchema(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор организации")
    name: str = Field(..., description="Название организации")
    description: str | None = Field(None, description="Описание организации")

    class Config:
        from_attributes = True


class OrganizationUpdateSchema(BaseModel):
    name: str | None = Field(None, description="Название организации")
    description: str | None = Field(None, description="Описание организации")