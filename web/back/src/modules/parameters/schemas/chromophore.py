from uuid import UUID
from pydantic import BaseModel, Field


class ChromophoreSchema(BaseModel):
    id: UUID = Field(..., description="ID хромофора")
    name: str = Field(..., description="Название хромофора")
    symbol: str = Field(..., description="Обозначение хромофора")
    description: str | None = Field(None, description="Описание хромофора")

    class Config:
        from_attributes = True


class ChromophoreUpdateSchema(BaseModel):
    name: str | None = Field(None, description="Новое название")
    symbol: str | None = Field(None, description="Новое обозначение")
    description: str | None = Field(None, description="Описание хромофора")
