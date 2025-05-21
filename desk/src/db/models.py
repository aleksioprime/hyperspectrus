import uuid
from datetime import datetime, date

from sqlalchemy import (
    create_engine, Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Date, Table
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# --- Ассоциативные таблицы ---

user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id')),
    Column('role_id', String(36), ForeignKey('roles.id'))
)

# --- Основные модели ---

class User(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_activity = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    organization = relationship("Organization", back_populates="users")
    sessions = relationship("Session", back_populates="operator")

class Role(Base):
    __tablename__ = 'roles'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String)
    users = relationship("User", secondary=user_roles, back_populates="roles")

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String)
    users = relationship("User", back_populates="organization")
    patients = relationship("Patient", back_populates="organization")

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    birth_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=True)
    sessions = relationship("Session", back_populates="patient")
    organization = relationship("Organization", back_populates="patients")

class DeviceBinding(Base):
    __tablename__ = 'device_bindings'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    device_id = Column(String(36), ForeignKey('devices.id'))
    ip_address = Column(String(100), nullable=False)

    user = relationship("User")
    device = relationship("Device")

class Device(Base):
    __tablename__ = 'devices'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    spectra = relationship("Spectrum", back_populates="device")
    sessions = relationship("Session", back_populates="device")

class Spectrum(Base):
    __tablename__ = 'spectra'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wavelength = Column(Integer, nullable=False)
    rgb_r = Column(Integer, nullable=True)
    rgb_g = Column(Integer, nullable=True)
    rgb_b = Column(Integer, nullable=True)
    device_id = Column(String(36), ForeignKey('devices.id'), nullable=False)
    device = relationship("Device", back_populates="spectra")
    overlaps = relationship("OverlapCoefficient", back_populates="spectrum")
    raw_images = relationship("RawImage", back_populates="spectrum")

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    device_id = Column(String(36), ForeignKey('devices.id'), nullable=False)
    device_task_id = Column(Integer, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    operator_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    notes = Column(String)

    patient = relationship("Patient", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")
    operator = relationship("User", back_populates="sessions")
    raw_images = relationship("RawImage", back_populates="session")
    reconstructed_images = relationship("ReconstructedImage", back_populates="session")
    result = relationship("Result", back_populates="session", uselist=False, single_parent=True)

class RawImage(Base):
    __tablename__ = 'raw_images'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False)
    spectrum_id = Column(String(36), ForeignKey('spectra.id'), nullable=False)
    file_path = Column(String, nullable=False)

    session = relationship("Session", back_populates="raw_images")
    spectrum = relationship("Spectrum", back_populates="raw_images")

class ReconstructedImage(Base):
    __tablename__ = 'reconstructed_images'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False)
    chromophore_id = Column(String(36), ForeignKey('chromophores.id'), nullable=False)
    file_path = Column(String, nullable=False)

    session = relationship("Session", back_populates="reconstructed_images")
    chromophore = relationship("Chromophore", back_populates="reconstructed_images")

class Chromophore(Base):
    __tablename__ = 'chromophores'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    symbol = Column(String, unique=True, nullable=False)
    overlaps = relationship("OverlapCoefficient", back_populates="chromophore")
    reconstructed_images = relationship("ReconstructedImage", back_populates="chromophore")

class OverlapCoefficient(Base):
    __tablename__ = 'overlap_coefficients'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    spectrum_id = Column(String(36), ForeignKey('spectra.id'), nullable=False)
    chromophore_id = Column(String(36), ForeignKey('chromophores.id'), nullable=False)
    coefficient = Column(Float, nullable=False)

    spectrum = relationship("Spectrum", back_populates="overlaps")
    chromophore = relationship("Chromophore", back_populates="overlaps")

class Result(Base):
    __tablename__ = 'results'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), unique=True)
    contour_path = Column(String, nullable=True)
    s_coefficient = Column(Float, nullable=False)
    mean_lesion_thb = Column(Float, nullable=False)
    mean_skin_thb = Column(Float, nullable=False)
    notes = Column(String)

    session = relationship("Session", back_populates="result")
