from uuid import UUID
from typing import List

from pydantic import BaseModel, Field


class RawImageSchema(BaseModel):
    """
    Схема для отображения информации об исходных изображениях
    """
    id: UUID = Field(..., description="ID исходного изображения")
    session_id: UUID = Field(..., description="ID сеанса")
    spectrum_id: UUID = Field(..., description="ID длины волны")
    file_path: str = Field(..., description="Путь к файлу изображения")

    class Config:
        from_attributes = True


class RawImageUpdateSchema(BaseModel):
    """
    Схема для редактирования информации об исходном изображении
    """
    spectrum_id: UUID | None = Field(None, description="Новый ID длины волны")
    file_path: str | None = Field(None, description="Новый путь к файлу изображения")


class RawImageIdsSchema(BaseModel):
    ids: List[UUID]
