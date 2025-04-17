from uuid import UUID
from pydantic import BaseModel, Field


class SpectrumSchema(BaseModel):
    id: UUID = Field(..., description="ID спектра")
    wavelength: int = Field(..., description="Длина волны (в нм)")
    device_id: UUID = Field(..., description="ID устройства")

    class Config:
        from_attributes = True


class SpectrumCreateSchema(BaseModel):
    wavelength: int = Field(..., description="Длина волны (в нм)")
    device_id: UUID = Field(..., description="ID устройства")


class SpectrumUpdateSchema(BaseModel):
    wavelength: int | None = Field(None, description="Новая длина волны")
    device_id: UUID | None = Field(None, description="Новый ID устройства")