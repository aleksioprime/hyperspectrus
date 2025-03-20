from abc import ABC, abstractmethod
from uuid import UUID
from typing import List
import logging

from sqlalchemy import update, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.user import User, user_roles
from src.models.role import Role
from src.repositories.base import BaseSQLRepository
from src.schemas.user import UserUpdateSchema

logger = logging.getLogger(__name__)

class BaseUserRepository(ABC):

    @abstractmethod
    async def update(self, user_id: UUID, body: UserUpdateSchema):
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

    async def update(self, user_id: UUID, body: UserUpdateSchema):
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

    async def role_add(self, user_id: UUID, role_id: UUID):
        """
        Добавляет роль пользователю, если она ещё не назначена
        """
        user_query = await self.session.execute(select(User).filter_by(id=user_id))
        user = user_query.scalars().first()
        if not user:
            raise NoResultFound(f"Пользователь с ID {user_id} не найден!")

        role_query = await self.session.execute(select(Role).filter_by(id=role_id))
        role = role_query.scalars().first()
        if not role:
            raise NoResultFound(f"Роль с ID {role_id} не найдена!")

        existing_role_query = await self.session.execute(
            select(user_roles).filter_by(user_id=user_id, role_id=role_id)
        )
        existing_role = existing_role_query.first()
        if existing_role:
            logger.warning(f"Пользователь {user_id} уже имеет роль {role_id}. Пропускаем")
            return

        stmt = insert(user_roles).values(user_id=user_id, role_id=role_id)

        await self.session.execute(stmt)
        logger.info(f"Роль {role_id} добавлена пользователю {user_id}!")

    async def role_remove(self, user_id: UUID, role_id: UUID):
        """
        Удаляет роль у пользователя, если она назначена.
        """
        user_query = await self.session.execute(select(User).filter_by(id=user_id))
        user = user_query.scalars().first()
        if not user:
            raise NoResultFound(f"Пользователь с ID {user_id} не найден!")

        role_query = await self.session.execute(select(Role).filter_by(id=role_id))
        role = role_query.scalars().first()
        if not role:
            raise NoResultFound(f"Роль с ID {role_id} не найдена!")

        existing_role_query = await self.session.execute(
            select(user_roles).filter_by(user_id=user_id, role_id=role_id)
        )
        existing_role = existing_role_query.first()
        if not existing_role:
            logger.warning(f"Пользователь {user_id} не имеет роли {role_id}. Нечего удалять")
            return

        stmt = delete(user_roles).filter_by(user_id=user_id, role_id=role_id)

        await self.session.execute(stmt)
        logger.info(f"Роль {role_id} удалена у пользователя {user_id}!")
