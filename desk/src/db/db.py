import os
from contextlib import contextmanager
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


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def has_users():
    """Checks if there are any users in the database."""
    from .models import User  # Local import to avoid circular dependency if models import db
    with get_db_session() as session:
        return session.query(User).first() is not None