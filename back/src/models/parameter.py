import uuid

from sqlalchemy import Column, String, Float, func, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime

from src.db.postgres import Base


class Spectrum(Base):
    """
    Модель спектра, содержащая длину волны и название спектра
    """
    __tablename__ = 'spectrum'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False) # Название спектра
    wavelength_nm = Column(Integer, nullable=False) # Длина волны спектра (в нанометрах)


class Chromophore(Base):
    """
    Модель хромофора, содержащая его название, обозначение и заметку
    """
    __tablename__ = 'chromophore'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False) # Название хромофора
    symbol = Column(String, unique=True, nullable=False) # Обозначение хромофора


class ChromophoreSpectrum(Base):
    """
    Модель спектра хромофора, содержащая коэффициент экстинкции
    """
    __tablename__ = 'chromophore_spectrum'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chromophore_id = Column(UUID(as_uuid=True), ForeignKey('chromophore.id'), nullable=False) # Связь с хромофором
    spectrum_id = Column(UUID(as_uuid=True), ForeignKey('spectrum.id')) # Связь со спектром
    extinction_coefficient = Column(Float, nullable=False) # Коэффициент экстинкции

    chromophore = relationship("Chromophore", back_populates="chromophore_spectra")
    spectrum = relationship("Spectrum", back_populates="chromophore_spectra")


class LED(Base):
    """
    Модель светодиода, содержащая его название, центральную длину волны и заметку
    """
    __tablename__ = 'led'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False) # Название светодиода
    central_wavelength_nm = Column(Integer, nullable=False) # Центральная длина волны светодиода (в нанометрах)

    spectra = relationship("LEDSpectrum", back_populates="led")


class LEDSpectrum(Base):
    """
    Модель спектра светодиода, содержащая его интенсивность излучения
    """
    __tablename__ = 'led_spectrum'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    led_id = Column(UUID(as_uuid=True), ForeignKey('led.id'), nullable=False) # Связь со светодиодом
    spectrum_id = Column(UUID(as_uuid=True), ForeignKey('spectrum.id'), nullable=False) # Связь со спектром
    emission_intensity = Column(Float, nullable=False) # Интенсивность излучения

    led = relationship("LED", back_populates="spectra")
    spectrum = relationship("Spectrum", back_populates="led_spectra")


# Связующие таблицы для многие ко многим между параметрами и светодиодами
parameter_led_association = Table(
    'parameter_led_association', Base.metadata,
    Column('parameter_set_id', UUID(as_uuid=True), ForeignKey('parameter_set.id')),
    Column('led_id', UUID(as_uuid=True), ForeignKey('led.id'))
)


# Связующие таблицы для многие ко многим между параметрами и хромофорами
parameter_chromophore_association = Table(
    'parameter_chromophore_association', Base.metadata,
    Column('parameter_set_id', UUID(as_uuid=True), ForeignKey('parameter_set.id')),
    Column('chromophore_id', UUID(as_uuid=True), ForeignKey('chromophore.id'))
)


class ParameterSet(Base):
    """
    Модель набора параметров, содержащая название и связи с хромофорами и светодиодами
    """
    __tablename__ = 'parameter_set'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    leds = relationship("LED", secondary=parameter_led_association)
    chromophores = relationship("Chromophore", secondary=parameter_chromophore_association)
    sessions = relationship("Session", back_populates="parameter_set")