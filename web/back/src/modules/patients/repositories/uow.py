from src.db.postgres import async_session_maker
from src.modules.patients.repositories.patient import PatientRepository
from src.modules.patients.repositories.session import SessionRepository
from src.modules.patients.repositories.raw_image import RawImageRepository
from src.modules.patients.repositories.result import ResultRepository


class UnitOfWork:
    def __init__(self):
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()
        self.patient = PatientRepository(self.session)
        self.session_repo = SessionRepository(self.session)
        self.raw_image = RawImageRepository(self.session)
        self.result = ResultRepository(self.session)

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()