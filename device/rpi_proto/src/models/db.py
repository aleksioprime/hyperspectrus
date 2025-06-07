import os
import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

"""
Модели базы данных и инициализация SQLite для хранения задач и фотографий.
"""

Base = declarative_base()

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.db"))
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class PhotoTask(Base):
    """
    Модель задачи на фотосессию: название, список спектров, статус, время создания.
    """
    __tablename__ = 'photo_tasks'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    spectra = Column(JSON, nullable=False) # [{'id': '...', 'rgb': [R,G,B]}, ...]
    status = Column(String, default="pending")  # pending/completed
    photos = relationship("Photo", back_populates="task", cascade="all, delete-orphan")

class Photo(Base):
    """
    Фото, привязанное к задаче (task), содержит путь, индекс и время съемки.
    """
    __tablename__ = 'photos'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    path = Column(String, nullable=False)
    task_id = Column(String(36), ForeignKey('photo_tasks.id'), nullable=False)
    spectrum_id = Column(String, nullable=False)
    taken_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("PhotoTask", back_populates="photos")

def init_db():
    """
    Инициализация БД: создание всех таблиц при первом запуске.
    """
    Base.metadata.create_all(engine)
