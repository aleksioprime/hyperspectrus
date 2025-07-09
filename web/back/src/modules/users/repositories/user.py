from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Tuple
import logging

from sqlalchemy import update, select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound
from werkzeug.security import generate_password_hash

from src.models.user import User, UserRoles, Role
from src.modules.users.repositories.base import BaseSQLRepository
from src.modules.users.schemas.user import UserUpdateSchema, UpdatePasswordUserSchema, UserQueryParams

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
        query = (
            select(User)
            .options(
                joinedload(User.roles),
                joinedload(User.organization),
                )
            .filter(User.id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def get_user_all(self, params: UserQueryParams) -> Tuple[List[User], int]:
        """ Получает список всех пользователей с предзагрузкой ролей """
        query = select(User).options(
            joinedload(User.roles),
            joinedload(User.organization)
        )

        if params.organization_id is not None:
            query = query.where(User.organization_id == params.organization_id)

        query = query.limit(params.limit).offset(params.offset)

        result = await self.session.execute(query)
        users = result.scalars().unique().all()
        total = await self._count_all_users(params.organization_id)
        return users, total

    async def _count_all_users(self, organization_id=None) -> int:
        """ Получает количество пользователей """
        query = select(func.count()).select_from(User)
        if organization_id is not None:
            query = query.where(User.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, user: User, role_ids: list[UUID] = None) -> None:
        """ Добавляет нового пользователя в текущую сессию """
        if role_ids:
            roles = await self.get_roles_by_ids(role_ids)
            user.roles = roles
        else:
            default_role = await self.get_or_create_default_role()
            user.roles = [default_role]
        self.session.add(user)

    async def update(self, user_id: UUID, body: UserUpdateSchema) -> User:
        """ Обновляет пользователя по его ID """
        update_data = {key: value for key, value in body.dict(exclude_unset=True, exclude={'roles'}).items()}
        if not update_data and not getattr(body, "roles", None):
            raise NoResultFound("Нет данных для обновления")

        user = await self.get_user_by_id(user_id)
        if not user:
            raise NoResultFound(f"Пользователь с ID {user_id} не найден")

        # Обновление обычных полей
        for key, value in update_data.items():
            setattr(user, key, value)

        # Обновление ролей
        if getattr(body, "roles", None) is not None:
            roles = await self.get_roles_by_ids(body.roles)
            user.roles = roles

        await self.session.flush()
        return user

    async def delete(self, user_id: UUID) -> None:
        """ Удаляет пользователя по его ID """
        result = await self.get_user_by_id(user_id)
        if not result:
            raise NoResultFound(f"Пользователь с ID {user_id} не найден")

        await self.session.delete(result)

    async def has_role(self, user_id: UUID, role_id: UUID) -> bool:
        """ Проверяет, есть ли у пользователя роль с указанным ID """
        query = select(UserRoles).filter_by(user_id=user_id, role_id=role_id)
        result = await self.session.execute(query)
        return result.first() is not None

    async def get_or_create_default_role(self) -> Role:
        """ Получает или создает роль по умолчанию """
        query = select(Role).filter_by(name="employee")
        role = await self.session.scalar(query)

        if not role:
            role = Role(name="employee", display_name="Сотрудник", description="Сотрудник организации")
            self.session.add(role)
            await self.session.flush()

        return role

    async def update_password(self, user_id: UUID, body: UpdatePasswordUserSchema) -> None:
        """ Обновляет пароль пользователя по его ID """
        if not body.password:
            raise NoResultFound("Нет данных для обновления")

        hashed_password = generate_password_hash(body.password)

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=hashed_password)
        )
        await self.session.execute(stmt)

    async def update_photo(self, user_id: UUID, photo: str) -> None:
        """ Обновляет фотографию пользователя по его ID """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(photo=photo)
        )
        await self.session.execute(stmt)

    async def get_roles_by_ids(self, role_ids: list[UUID]) -> list[Role]:
        """
        Получение ролей по списку UUID
        """
        if not role_ids:
            return []
        query = select(Role).where(Role.id.in_(role_ids))
        result = await self.session.execute(query)
        return result.scalars().all()