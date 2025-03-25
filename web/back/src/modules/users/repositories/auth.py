from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from sqlalchemy import select

from src.models.user import User, Role
from src.modules.users.repositories.base import BaseSQLRepository


class BaseAuthRepository(ABC):
    ...


class AuthRepository(BaseAuthRepository, BaseSQLRepository):

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Получает пользователя по его имени
        """
        query = select(User).filter_by(username=username)
        result = await self.session.scalars(query)
        return result.one_or_none()

    async def get_roles_by_user(self, user_id: UUID) -> List[str]:
        """
        Получает список ролей по ID пользователя
        """
        query = (
            select(Role.name)
            .join(Role.users)
            .filter(User.id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()