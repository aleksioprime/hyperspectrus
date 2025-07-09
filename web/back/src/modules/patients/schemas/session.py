from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from pydantic import BaseModel, Field

from src.core.schemas import BasePaginationParams


class SessionQueryParams(BasePaginationParams):
    patient: UUID | None

    class Config:
        arbitrary_types_allowed = True


class SessionSchema(BaseModel):
    """
    Схема для отображения информации о сеансе
    """
    id: UUID = Field(..., description="Уникальный идентификатор сеанса")
    patient_id: UUID | None = Field(None, description="ID пациента")
    device_id: UUID = Field(..., description="ID устройства")
    date: datetime = Field(..., description="Дата и время сеанса")
    operator_id: UUID = Field(..., description="ID оператора")
    notes: str | None = Field(None, description="Дополнительные заметки")

    class Config:
        from_attributes = True


class SessionCreateSchema(BaseModel):
    """
    Схема для создания нового сеанса
    """
    patient_id: UUID | None = Field(None, description="ID пациента (может быть необязательным)")
    device_id: UUID = Field(..., description="ID устройства, используемого в сеансе")
    date: datetime | None = Field(None, description="Дата и время сеанса (по умолчанию — текущее время)")
    notes: str | None = Field(None, description="Дополнительные заметки к сеансу")

    class Config:
        from_attributes = True


class SessionUpdateSchema(BaseModel):
    """
    Схема для обновления сеанса (частичное обновление)
    """
    patient_id: UUID | None = Field(None, description="Новый ID пациента")
    device_id: UUID | None = Field(None, description="Новый ID устройства")
    date: datetime | None = Field(None, description="Новая дата и время сеанса")
    operator_id: UUID | None = Field(None, description="Новый ID оператора")
    notes: str | None = Field(None, description="Обновленные заметки")

    class Config:
        from_attributes = True


class SpectrumSchema(BaseModel):
    id: UUID = Field(..., description="ID спектра")
    wavelength: int = Field(..., description="Длина волны в нанометрах")
    name: str | None = Field(None, description="Название спектра")

    class Config:
        from_attributes = True


class RawImageSchema(BaseModel):
    id: UUID = Field(..., description="ID исходного изображения")
    file_path: str = Field(..., description="Путь к файлу изображения")
    spectrum: SpectrumSchema = Field(..., description="ID длины волны")

    class Config:
        from_attributes = True


class ReconstructedImageSchema(BaseModel):
    id: UUID = Field(..., description="ID восстановленного изображения")
    file_path: str = Field(..., description="Путь к файлу изображения")
    chromophore_id: UUID = Field(..., description="ID хромофора")

    class Config:
        from_attributes = True


class ResultSchema(BaseModel):
    id: UUID = Field(..., description="ID результата")
    contour_path: str | None = Field(None, description="Путь к файлу с контуром пораженной области")
    s_coefficient: float = Field(..., description="Коэффициент s")
    mean_lesion_thb: float = Field(..., description="Средняя концентрация THb в поражённой области")
    mean_skin_thb: float = Field(..., description="Средняя концентрация THb в коже")
    notes: str | None = Field(None, description="Дополнительные заметки")

    class Config:
        from_attributes = True


class DeviceSchema(BaseModel):
    id: UUID = Field(..., description="ID устройства")
    name: str = Field(..., description="Название модели устройства")

    class Config:
        from_attributes = True


class PatientSchema(BaseModel):
    id: UUID = Field(..., description="ID пациента")
    full_name: str = Field(..., description="ФИО пациента")
    birth_date: date = Field(..., description="Дата рождения пациента")
    notes: str | None = Field(None, description="Дополнительные заметки")

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    id: UUID = Field(..., description="ID оператора")
    first_name: str = Field(..., description="Имя оператора")
    last_name: str = Field(..., description="Фамилия оператора")

    class Config:
        from_attributes = True


class SessionDetailSchema(SessionSchema):
    """
    Расширенная схема сеанса с вложенными объектами
    """
    patient: PatientSchema | None = Field(None, description="Информация о пациенте")
    operator: UserSchema | None = Field(None, description="Информация об операторе")
    device: DeviceSchema = Field(..., description="Информация об используемом устройстве")
    raw_images: list[RawImageSchema] = Field(default_factory=list, description="Список исходных изображений")
    reconstructed_images: list[ReconstructedImageSchema] = Field(default_factory=list, description="Список восстановленных изображений")
    result: ResultSchema | None = Field(None, description="Результаты анализа сеанса (если есть)")
