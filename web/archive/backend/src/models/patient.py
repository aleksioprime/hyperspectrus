import uuid

from sqlalchemy import Column, String, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, Date

from src.db.postgres import Base
from src.models.image import RawImage, ReconstructedImage
from src.models.parameter import Device
from src.models.result import Result


class Patient(Base):
    """
    Модель пациента. Содержит основную информацию о пациенте,
    а также связанные сессии (сеансы исследований).
    """
    __tablename__ = 'patient'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=False)  # Имя пациента
    birth_date = Column(Date, nullable=False)  # Дата рождения
    created_at = Column(DateTime(timezone=True), default=func.now())  # Дата создания записи
    notes = Column(String, nullable=True)  # Дополнительные заметки
    organization_id = Column(UUID(as_uuid=True), nullable=True) # ID организации

    sessions = relationship("Session", back_populates="patient")

    def __repr__(self) -> str:
        return f'<Patient {self.name}>'


class Session(Base):
    """
    Модель сеанса исследования пациента. Связана с пациентом, девайсом,
    оператором, а также содержит результаты анализа и изображения.
    """
    __tablename__ = 'session'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patient.id'))  # Связь с пациентом
    device_id = Column(UUID(as_uuid=True), ForeignKey('device.id'), nullable=False)  # Связь с девайсом
    date = Column(DateTime(timezone=True), default=func.now())  # Дата и время сеанса
    operator_id = Column(UUID(as_uuid=True), nullable=False)  # ID оператора
    notes = Column(String)  # Дополнительные заметки

    patient = relationship("Patient", back_populates="sessions")
    raw_images = relationship("RawImage", back_populates="session")
    reconstructed_images = relationship("ReconstructedImage", back_populates="session")
    device = relationship("Device", back_populates="sessions")
    result = relationship("Result", back_populates="session", uselist=False)