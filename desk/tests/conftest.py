import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from desk.src.db.models import Base # Adjusted import path

@pytest.fixture(scope="function") # function scope for full isolation
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False) # Added autoflush and expire_on_commit
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback() # Ensure any uncommitted changes are rolled back
        session.close()
        Base.metadata.drop_all(engine) # Drop all tables
        engine.dispose()
