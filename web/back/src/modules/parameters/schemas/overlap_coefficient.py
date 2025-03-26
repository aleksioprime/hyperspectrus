from uuid import UUID
from pydantic import BaseModel, Field


class OverlapCoefficientSchema(BaseModel):
    id: UUID = Field(..., description="ID коэффициента перекрытия")
    spectrum_id: UUID = Field(..., description="ID спектра")
    chromophore_id: UUID = Field(..., description="ID хромофора")
    coefficient: float = Field(..., description="Коэффициент перекрытия")

    class Config:
        from_attributes = True


class OverlapCoefficientCreateSchema(BaseModel):
    spectrum_id: UUID = Field(..., description="ID спектра")
    chromophore_id: UUID = Field(..., description="ID хромофора")
    coefficient: float = Field(..., description="Коэффициент перекрытия")


class OverlapCoefficientUpdateSchema(BaseModel):
    spectrum_id: UUID | None = Field(None, description="Новый ID спектра")
    chromophore_id: UUID | None = Field(None, description="Новый ID хромофора")
    coefficient: float | None = Field(None, description="Новый коэффициент")
