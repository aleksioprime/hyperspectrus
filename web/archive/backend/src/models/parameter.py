import uuid

from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.postgres import Base


class Device(Base):
    """
    Модель устройства, содержащая его название и связь с спектрами светодиодов
    """
    __tablename__ = 'device'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)  # Модель устройства

    spectrums = relationship("Spectrum", back_populates="device")
    sessions = relationship("Session", back_populates="device")


class Spectrum(Base):
    """
    Модель спектра светодиода, содержащая его интенсивность излучения
    """
    __tablename__ = 'spectrum'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wavelength = Column(Integer, nullable=False) # Длина волны спектра (в нанометрах)
    device_id = Column(UUID(as_uuid=True), ForeignKey('device.id'), nullable=False)  # Связь с устройством

    device = relationship("Device", back_populates="spectrums")
    overlaps = relationship("OverlapCoefficient", back_populates="spectrum")


class Chromophore(Base):
    """
    Модель хромофора, содержащая его название, обозначение и заметку
    """
    __tablename__ = 'chromophore'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False) # Название хромофора
    symbol = Column(String, unique=True, nullable=False) # Обозначение хромофора

    overlaps = relationship("OverlapCoefficient", back_populates="chromophore")
    reconstructed_images = relationship("ReconstructedImage", back_populates="chromophore")


class OverlapCoefficient(Base):
    __tablename__ = 'overlap_coefficient'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spectrum_id = Column(UUID(as_uuid=True), ForeignKey('spectrum.id'), nullable=False)
    chromophore_id = Column(UUID(as_uuid=True), ForeignKey('chromophore.id'), nullable=False)
    coefficient = Column(Float, nullable=False)  # Коэффициент перекрытия

    # Связи с основными таблицами
    spectrum = relationship("Spectrum", back_populates="overlaps")
    chromophore = relationship("Chromophore", back_populates="overlaps")