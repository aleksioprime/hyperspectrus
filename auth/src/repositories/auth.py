from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select

from src.models.user import User
from src.models.role import Role
from src.repositories.base import BaseSQLRepository
from src.schemas.auth import RegisterSchema


class BaseAuthRepository(ABC):

    @abstractmethod
    async def register(self, body: RegisterSchema) -> User:
        ...


class AuthRepository(BaseAuthRepository, BaseSQLRepository):

    async def register(self, body: RegisterSchema) -> User:
        user = User(
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            login=body.login,
            password=body.password,
        )

        # Получаем или создаем роль "User"
        query = select(Role).filter_by(name="user")
        role = await self.session.scalar(query)

        if not role:
            role = Role(name="user", description="Default user role")
            self.session.add(role)
            await self.session.flush()

        # Присваиваем пользователю роль "user"
        user.roles.append(role)

        # Сохраняем пользователя в базе
        self.session.add(user)
        await self.session.flush()

        return user

    async def get_user_by_login(self, login: str):
        query = select(User).filter_by(login=login)
        result = await self.session.scalars(query)
        return result.one_or_none()

    async def get_roles(self, user_id: UUID):
        """
        Получает список ролей пользователя по его ID
        """
        query = (
            select(Role.name)
            .join(Role.users)
            .filter(User.id == user_id)
        )
        result = await self.session.execute(query)
        roles = result.scalars().all()
        return roles