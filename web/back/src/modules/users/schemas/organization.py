from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationSchema(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор организации")
    name: str = Field(..., description="Название организации")
    description: str = Field(..., description="Описание организации")

    class Config:
        from_attributes = True


class OrganizationUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Название организации")
    description: Optional[str] = Field(None, description="Описание организации")