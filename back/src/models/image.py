import uuid

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.postgres import Base


class RawImage(Base):
    """
    Исходное изображение, связанное с сеансом.
    Включает длину волны и путь к файлу изображения
    """
    __tablename__ = 'raw_image'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('session.id'))  # Связь с сеансом
    wavelength_nm = Column(Integer, nullable=False)  # Длина волны
    file_path = Column(String, nullable=False)  # Путь к файлу изображения

    session = relationship("Session", back_populates="raw_images")


class ReconstructedImage(Base):
    """
    Восстановленное изображение, связанное с сеансом.
    Содержит информацию о хромофоре и путь к файлу изображения
    """
    __tablename__ = 'reconstructed_image'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('session.id'))  # Связь с сеансом
    chromophore_id = Column(UUID(as_uuid=True), ForeignKey('chromophore.id'))  # Связь с хромофором
    file_path = Column(String, nullable=False)  # Путь к файлу изображения

    session = relationship("Session", back_populates="reconstructed_images")
    chromophore = relationship("Chromophore", back_populates="reconstructed_images")