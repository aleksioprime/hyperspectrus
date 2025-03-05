from abc import ABC, abstractmethod
from uuid import UUID
from typing import List

from sqlalchemy import update, delete, insert
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.user import User, user_roles
from src.repositories.base import BaseSQLRepository
from src.schemas.user import UserUpdate


class BaseUserRepository(ABC):

    @abstractmethod
    async def update(self, user_id: UUID, body: UserUpdate):
        ...


class UserRepository(BaseUserRepository, BaseSQLRepository):

    async def get_user_by_id(self, user_id: UUID):
        """
        Получает пользователя по его ID
        """
        query = (
            select(User)
            .options(joinedload(User.roles))
            .filter(User.id == user_id)
        )
        result = await self.session.execute(query)
        user = result.scalars().unique().one_or_none()
        return user

    async def get_user_all(self):
        """
        Получает всех пользователей
        """
        query = select(User).options(joinedload(User.roles))
        result = await self.session.execute(query)
        users = result.scalars().unique().all()
        return users

    async def update(self, user_id: UUID, body: UserUpdate):
        """
        Обновляет данные пользователя
        """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound(f"Нет данных")

        query = (
            update(User)
            .filter_by(id=user_id)
            .values(**update_data)
        )
        await self.session.execute(query)

        updated_user = await self.get_user_by_id(user_id)

        return updated_user

    async def delete(self, user_id: UUID) -> None:
        """
        Удаляет пользователя по его ID
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NoResultFound(f"Пользователь с ID {user_id} не найден")

        await self.session.delete(user)
        await self.session.flush()
