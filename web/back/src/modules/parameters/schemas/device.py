from uuid import UUID
from pydantic import BaseModel, Field


class DeviceSchema(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор устройства")
    name: str = Field(..., description="Название модели устройства")

    class Config:
        from_attributes = True


class DeviceCreateSchema(BaseModel):
    name: str = Field(..., description="Название новой модели устройства")


class DeviceUpdateSchema(BaseModel):
    name: str | None = Field(None, description="Новое название устройства")


class ChromophoreSchema(BaseModel):
    id: UUID = Field(..., description="ID хромофора")
    name: str = Field(..., description="Название хромофора")
    symbol: str = Field(..., description="Обозначение хромофора")

    class Config:
        from_attributes = True


class OverlapCoefficientSchema(BaseModel):
    id: UUID = Field(..., description="ID коэффициента перекрытия")
    chromophore_id: UUID = Field(..., description="ID хромофора")
    coefficient: float = Field(..., description="Коэффициент перекрытия")

    class Config:
        from_attributes = True


class SpectrumSchema(BaseModel):
    id: UUID = Field(..., description="ID спектра")
    wavelength: int = Field(..., description="Длина волны в нанометрах")
    name: str | None = Field(None, description="Название спектра")
    overlaps: list[OverlapCoefficientSchema] = Field(default_factory=list, description="Коэффициенты перекрытия для хромофоров")

    class Config:
        from_attributes = True


class DeviceDetailSchema(DeviceSchema):
    spectra: list[SpectrumSchema] = Field(default_factory=list, description="Список спектров, связанных с устройством")
