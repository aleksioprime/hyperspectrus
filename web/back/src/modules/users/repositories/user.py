from abc import ABC, abstractmethod
from uuid import UUID
from typing import List
import logging

from sqlalchemy import update, delete, insert, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.user import User, UserRoles, Role
from src.modules.users.repositories.base import BaseSQLRepository
from src.modules.users.schemas.user import UserUpdateSchema, UserQueryParams

logger = logging.getLogger(__name__)

class BaseUserRepository(ABC):

    @abstractmethod
    async def update(self, user_id: UUID, body: UserUpdateSchema):
        ...


class UserRepository(BaseUserRepository, BaseSQLRepository):

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """
        Получает пользователя по его ID
        """
        query = select(User).filter(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def get_user_with_roles(self, user_id: UUID) -> User | None:
        """ Получает пользователя по его ID вместе с ролями """
        query = (
            select(User)
            .options(joinedload(User.roles))
            .filter(User.id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def get_user_all(self, params: UserQueryParams) -> List[User]:
        """ Получает список всех пользователей с предзагрузкой ролей """
        query = (
            select(User)
            .options(joinedload(User.roles))
            .limit(params.limit)
            .offset(params.offset)
        )
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def create(self, user: User) -> None:
        """ Добавляет нового пользователя в текущую сессию """
        self.session.add(user)

    async def update(self, user_id: UUID, body: UserUpdateSchema) -> User:
        """ Обновляет пользователя по его ID """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound("Нет данных для обновления")

        stmt = (
            update(User)
            .filter_by(id=user_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_user_by_id(user_id)

    async def delete(self, user_id: UUID) -> None:
        """ Удаляет пользователя по его ID """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NoResultFound(f"Пользователь с ID {user_id} не найден")

        await self.session.delete(user)

    async def has_role(self, user_id: UUID, role_id: UUID) -> bool:
        """ Проверяет, есть ли у пользователя роль с указанным ID """
        query = select(UserRoles).filter_by(user_id=user_id, role_id=role_id)
        result = await self.session.execute(query)
        return result.first() is not None

    async def get_role(self, role_id: UUID) -> Role | None:
        """ Получает роль по её ID """
        query = select(Role).filter_by(id=role_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def add_role(self, user_id: UUID, role_id: UUID) -> None:
        """ Добавляет роль к пользователю """
        stmt = insert(UserRoles).values(user_id=user_id, role_id=role_id)
        await self.session.execute(stmt)

    async def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        """ Удаляет роль у пользователя """
        stmt = delete(UserRoles).filter_by(user_id=user_id, role_id=role_id)
        await self.session.execute(stmt)

    async def get_or_create_default_role(self) -> Role:
        """ Получает или создает роль по умолчанию """
        query = select(Role).filter_by(name="user")
        role = await self.session.scalar(query)

        if not role:
            role = Role(name="user", description="Default user role")
            self.session.add(role)
            await self.session.flush()

        return role