from src.db.postgres import async_session_maker

from src.modules.users.repositories.auth import AuthRepository
from src.modules.users.repositories.user import UserRepository
from src.modules.users.repositories.role import RoleRepository
from src.modules.users.repositories.organization import OrganizationRepository


class UnitOfWork:
    def __init__(self):
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()
        self.auth = AuthRepository(self.session)
        self.user = UserRepository(self.session)
        self.role = RoleRepository(self.session)
        self.organization = OrganizationRepository(self.session)

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