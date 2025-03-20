import uuid

from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.postgres import Base


class Result(Base):
    """
    Модель результата анализа, содержащая путь к файлу с контуром поражения,
    коэффициент s, среднюю концентрацию THb в пораженной области и коже
    """
    __tablename__ = 'result'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('session.id'))  # Связь с сеансом
    contour_path = Column(String, nullable=False)  # Путь к файлу с контуром пораженной области
    s_coefficient = Column(Float, nullable=False)  # Коэффициент s
    mean_lesion_thb = Column(Float, nullable=False)  # Средняя концентрация THb в пораженной области
    mean_skin_thb = Column(Float, nullable=False)  # Средняя концентрация THb в коже
    notes = Column(String)  # Дополнительные заметки

    session = relationship("Session", back_populates="result")