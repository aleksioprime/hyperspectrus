from uuid import UUID
from pydantic import BaseModel, Field

class OverlapCoefficientSchema(BaseModel):
    id: UUID = Field(..., description="ID коэффициента перекрытия")
    chromophore_id: UUID = Field(..., description="ID хромофора")
    coefficient: float = Field(..., description="Коэффициент перекрытия")

    class Config:
        from_attributes = True

class SpectrumSchema(BaseModel):
    id: UUID = Field(..., description="ID спектра")
    wavelength: int = Field(..., description="Длина волны (в нм)")
    name: str | None = Field(None, description="Название спектра")
    device_id: UUID = Field(..., description="ID устройства")
    overlaps: list[OverlapCoefficientSchema] = Field(default_factory=list, description="Коэффициенты перекрытия для хромофоров")

    class Config:
        from_attributes = True


class SpectrumCreateSchema(BaseModel):
    wavelength: int = Field(..., description="Длина волны (в нм)")
    name: str | None = Field(None, description="Название спектра")


class SpectrumUpdateSchema(BaseModel):
    wavelength: int | None = Field(None, description="Новая длина волны")
    name: str | None = Field(None, description="Название спектра")
