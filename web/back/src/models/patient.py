import uuid

from sqlalchemy import Column, String, func, ForeignKey, Float, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.postgres import Base


class Patient(Base):
    """
    Модель пациента. Содержит основную информацию о пациенте,
    а также связанные сессии (сеансы исследований).
    """
    __tablename__ = 'patients'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)  # Имя пациента
    birth_date = Column(Date, nullable=False)  # Дата рождения
    created_at = Column(DateTime(timezone=True), default=func.now())  # Дата создания записи
    notes = Column(String, nullable=True)  # Дополнительные заметки
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=True) # ID организации

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

    patient = relationship("Patient", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")
    operator = relationship("User", back_populates="sessions")
    raw_images = relationship("RawImage", back_populates="session")
    reconstructed_images = relationship("ReconstructedImage", back_populates="session")
    result = relationship("Result", back_populates="session", uselist=False, single_parent=True)


class RawImage(Base):
    """
    Исходное изображение, связанное с сеансом.
    Включает длину волны и путь к файлу изображения
    """
    __tablename__ = 'raw_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'))  # Связь с сеансом
    spectrum_id = Column(UUID(as_uuid=True), ForeignKey('spectra.id'))  # Связь с длиной волны
    file_path = Column(String, nullable=False)  # Путь к файлу изображения

    session = relationship("Session", back_populates="raw_images")


class ReconstructedImage(Base):
    """
    Восстановленное изображение, связанное с сеансом.
    Содержит информацию о хромофоре и путь к файлу изображения
    """
    __tablename__ = 'reconstructed_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'))  # Связь с сеансом
    chromophore_id = Column(UUID(as_uuid=True), ForeignKey('chromophores.id'))  # Связь с хромофором
    file_path = Column(String, nullable=False)  # Путь к файлу изображения

    session = relationship("Session", back_populates="reconstructed_images")
    chromophore = relationship("Chromophore", back_populates="reconstructed_images")


class Result(Base):
    """
    Модель результата анализа, содержащая путь к файлу с контуром поражения,
    коэффициент s, среднюю концентрацию THb в пораженной области и коже
    """
    __tablename__ = 'results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), unique=True)  # Связь с сеансом
    contour_path = Column(String, nullable=True)  # Путь к файлу с контуром пораженной области
    s_coefficient = Column(Float, nullable=False)  # Коэффициент s
    mean_lesion_thb = Column(Float, nullable=False)  # Средняя концентрация THb в пораженной области
    mean_skin_thb = Column(Float, nullable=False)  # Средняя концентрация THb в коже
    notes = Column(String)  # Дополнительные заметки

    session = relationship("Session", back_populates="result")