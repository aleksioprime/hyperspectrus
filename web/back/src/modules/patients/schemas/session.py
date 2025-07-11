from uuid import UUID
from datetime import datetime, date

from pydantic import BaseModel, Field

from src.constants.celery import CeleryStatus

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
    Схема для обновления сеанса
    """
    date: datetime | None = Field(None, description="Новая дата и время сеанса")
    notes: str | None = Field(None, description="Обновленные заметки")

    class Config:
        from_attributes = True


class SpectrumSchema(BaseModel):
    """
    Схема для вложенного поля спектров
    """
    id: UUID = Field(..., description="ID спектра")
    wavelength: int = Field(..., description="Длина волны в нанометрах")
    name: str | None = Field(None, description="Название спектра")

    class Config:
        from_attributes = True


class RawImageSchema(BaseModel):
    """
    Схема для вложенного поля исходных изображений
    """
    id: UUID = Field(..., description="ID исходного изображения")
    file_path: str = Field(..., description="Путь к файлу изображения")
    spectrum: SpectrumSchema = Field(..., description="ID длины волны")

    class Config:
        from_attributes = True


class ChromophoreSchema(BaseModel):
    """
    Схема для вложенного поля хромофоров
    """
    id: UUID = Field(..., description="ID хромофора")
    name: str = Field(..., description="Название хромофора")
    symbol: str = Field(..., description="Обозначение хромофора")

    class Config:
        from_attributes = True


class ReconstructedImageSchema(BaseModel):
    """
    Схема для вложенного поля обработанных изображений
    """
    id: UUID = Field(..., description="ID восстановленного изображения")
    file_path: str = Field(..., description="Путь к файлу изображения")
    chromophore: ChromophoreSchema = Field(..., description="ID хромофора")

    class Config:
        from_attributes = True


class ResultSchema(BaseModel):
    """
    Схема для вложенного поля результата обработки
    """
    id: UUID = Field(..., description="ID результата")
    contour_path: str | None = Field(None, description="Путь к файлу с контуром пораженной области")
    s_coefficient: float = Field(..., description="Коэффициент s")
    mean_lesion_thb: float = Field(..., description="Средняя концентрация THb в поражённой области")
    mean_skin_thb: float = Field(..., description="Средняя концентрация THb в коже")

    class Config:
        from_attributes = True


class DeviceSchema(BaseModel):
    """
    Схема для вложенного поля устройства
    """
    id: UUID = Field(..., description="ID устройства")
    name: str = Field(..., description="Название модели устройства")

    class Config:
        from_attributes = True


class PatientSchema(BaseModel):
    """
    Схема для вложенного поля пациента
    """
    id: UUID = Field(..., description="ID пациента")
    full_name: str = Field(..., description="ФИО пациента")
    birth_date: date = Field(..., description="Дата рождения пациента")
    notes: str | None = Field(None, description="Дополнительные заметки")

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    """
    Схема для вложенного поля оператора
    """
    id: UUID = Field(..., description="ID оператора")
    first_name: str = Field(..., description="Имя оператора")
    last_name: str = Field(..., description="Фамилия оператора")

    class Config:
        from_attributes = True


class SessionDetailSchema(BaseModel):
    """
    Расширенная схема сеанса с вложенными объектами
    """
    id: UUID = Field(..., description="ID сессии")
    patient: PatientSchema | None = Field(None, description="Информация о пациенте")
    operator: UserSchema | None = Field(None, description="Информация об операторе")
    device: DeviceSchema = Field(..., description="Информация об используемом устройстве")
    raw_images: list[RawImageSchema] = Field(default_factory=list, description="Список исходных изображений")
    reconstructed_images: list[ReconstructedImageSchema] = Field(default_factory=list, description="Список восстановленных изображений")
    result: ResultSchema | None = Field(None, description="Результаты анализа сеанса (если есть)")
    date: datetime = Field(..., description="Дата и время сеанса")
    notes: str | None = Field(None, description="Дополнительные заметки")
    processing_task_id: str | None = Field(None, description="ID задачи Celery")
    processing_status: CeleryStatus | None = Field(
        None, description="Статус задачи обработки"
    )
