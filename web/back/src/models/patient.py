import uuid
import enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Column, String, func, ForeignKey, Float, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.postgres import Base
from src.constants.celery import CeleryStatus

class Patient(Base):
    """
    Модель пациента. Содержит основную информацию о пациенте,
    а также связанные сессии (сеансы исследований).
    """
    __tablename__ = 'patients'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    birth_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    notes = Column(String, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=True)

    sessions = relationship("Session", back_populates="patient")
    organization = relationship("Organization", back_populates="patients")

    def __repr__(self) -> str:
        return f'<Patient {self.full_name}>'


class Session(Base):
    """
    Модель сеанса исследования пациента. Связана с пациентом, девайсом,
    оператором, а также содержит результаты анализа и изображения.
    """
    __tablename__ = 'sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'))  # Связь с пациентом
    device_id = Column(UUID(as_uuid=True), ForeignKey('devices.id'), nullable=False)  # Связь с девайсом
    date = Column(DateTime(timezone=True), default=func.now())  # Дата и время сеанса
    operator_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)  # ID оператора
    notes = Column(String)  # Дополнительные заметки
    processing_task_id = Column(String, nullable=True)
    processing_status = Column(SAEnum(CeleryStatus), nullable=True)

    patient = relationship("Patient", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")
    operator = relationship("User", back_populates="sessions")
    raw_images = relationship("RawImage", back_populates="session", cascade="all, delete-orphan")
    reconstructed_images = relationship("ReconstructedImage", back_populates="session", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="session", uselist=False, single_parent=True, cascade="all, delete-orphan")


class RawImage(Base):
    """
    Исходное изображение, связанное с сеансом.
    Включает длину волны и путь к файлу изображения
    """
    __tablename__ = 'raw_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'))
    spectrum_id = Column(UUID(as_uuid=True), ForeignKey('spectra.id'))
    file_path = Column(String, nullable=False)

    session = relationship("Session", back_populates="raw_images")
    spectrum = relationship("Spectrum", back_populates="raw_images")


class ReconstructedImage(Base):
    """
    Восстановленное изображение, связанное с сеансом.
    Содержит информацию о хромофоре и путь к файлу изображения
    """
    __tablename__ = 'reconstructed_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'))
    chromophore_id = Column(UUID(as_uuid=True), ForeignKey('chromophores.id'))
    file_path = Column(String, nullable=False)

    session = relationship("Session", back_populates="reconstructed_images")
    chromophore = relationship("Chromophore", back_populates="reconstructed_images")


class Result(Base):
    """
    Модель результата анализа, содержащая путь к файлу с контуром поражения,
    коэффициент s, среднюю концентрацию THb в пораженной области и коже
    """
    __tablename__ = 'results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), unique=True)
    contour_path = Column(String, nullable=True)
    s_coefficient = Column(Float, nullable=False)
    mean_lesion_thb = Column(Float, nullable=False)
    mean_skin_thb = Column(Float, nullable=False)

    session = relationship("Session", back_populates="result")