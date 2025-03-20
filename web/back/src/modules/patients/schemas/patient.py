from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from pydantic import BaseModel, Field, validator

from src.schemas.base import BasePaginationParams


class PatientQueryParams(BasePaginationParams):
    organization: UUID | None

    class Config:
        arbitrary_types_allowed = True


class PatientSchema(BaseModel):
    """
    Схема для отображения информации о пациенте
    """
    id: UUID = Field(..., description="Уникальный идентификатор пациента")
    name: str = Field(..., description="ФИО пациента")
    birth_date: date = Field(..., description="Дата рождения пациента")

    class Config:
        from_attributes = True


class PatientCreateSchema(BaseModel):
    """
    Схема для создания пациента
    """
    name: str = Field(..., description="ФИО пациента")
    birth_date: date = Field(..., description="Дата рождения пациента")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")
    organization_id: UUID = Field(..., description="ID организации")

    @validator("birth_date", pre=True)
    def parse_birth_date(cls, value):
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"):  # Пробуем разные форматы
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError("Неверный формат даты. Ожидаемые форматы: YYYY-MM-DD, DD-MM-YYYY, MM-DD-YYYY.")
        return value


class PatientUpdateSchema(BaseModel):
    """
    Схема для обновления информации о пациенте
    """
    name: Optional[str] = Field(None, description="ФИО пациента")
    birth_date: Optional[date] = Field(None, description="Дата рождения пациента")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")


class SessionSchema(BaseModel):
    """
    Схема сессии (сеанса исследования)
    """
    id: UUID = Field(..., description="Уникальный идентификатор сессии")
    date: datetime = Field(..., description="Дата проведения сессии")
    notes: Optional[str] = Field(None, description="Дополнительные заметки о сессии")

    class Config:
        from_attributes = True


class PatientDetailSchema(BaseModel):
    """
    Детальная схема пациента (включает всю информацию и связанные сессии)
    """
    id: UUID = Field(..., description="Уникальный идентификатор пациента")
    name: str = Field(..., description="ФИО пациента")
    birth_date: datetime = Field(..., description="Дата рождения пациента")
    created_at: datetime = Field(..., description="Дата создания записи")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")
    sessions: List[SessionSchema] = Field(..., description="Список сеансов пациента")

    class Config:
        from_attributes = True