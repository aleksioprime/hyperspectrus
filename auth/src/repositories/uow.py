from src.db.postgres import async_session_maker
from src.repositories.auth import AuthRepository
from src.repositories.user import UserRepository


class UnitOfWork:
    def __init__(self):
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()
        self.auth = AuthRepository(self.session)
        self.user = UserRepository(self.session)

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