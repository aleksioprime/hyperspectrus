from uuid import UUID
from pydantic import BaseModel, Field


class ResultSchema(BaseModel):
    """
    Схема для отображения информации о результате анализа
    """
    id: UUID = Field(..., description="ID результата")
    session_id: UUID = Field(..., description="ID сеанса")
    contour_path: str | None = Field(None, description="Путь к файлу с контуром поражённой области")
    s_coefficient: float = Field(..., description="Коэффициент s")
    mean_lesion_thb: float = Field(..., description="Средняя концентрация THb в поражённой области")
    mean_skin_thb: float = Field(..., description="Средняя концентрация THb в коже")
    notes: str | None = Field(None, description="Дополнительные заметки")

    class Config:
        from_attributes = True


class ResultCreateSchema(BaseModel):
    """
    Схема для создания результата анализа
    """
    session_id: UUID = Field(..., description="ID сеанса")
    contour_path: str | None = Field(None, description="Путь к файлу с контуром поражённой области")
    s_coefficient: float = Field(..., description="Коэффициент s")
    mean_lesion_thb: float = Field(..., description="Средняя концентрация THb в поражённой области")
    mean_skin_thb: float = Field(..., description="Средняя концентрация THb в коже")
    notes: str | None = Field(None, description="Дополнительные заметки")


class ResultUpdateSchema(BaseModel):
    """
    Схема для редактирования информации о результате анализа
    """
    contour_path: str | None = Field(None, description="Новый путь к файлу с контуром")
    s_coefficient: float | None = Field(None, description="Новый коэффициент s")
    mean_lesion_thb: float | None = Field(None, description="Новая концентрация THb в поражённой области")
    mean_skin_thb: float | None = Field(None, description="Новая концентрация THb в коже")
    notes: str | None = Field(None, description="Новые дополнительные заметки")