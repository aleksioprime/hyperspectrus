import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base

# Вычисляем путь к app.db относительно main.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "app.db")

engine = create_engine(f"sqlite:///{db_path}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def init_db():
    Base.metadata.create_all(engine)