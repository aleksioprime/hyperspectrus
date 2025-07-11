from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import update, select
from sqlalchemy.exc import NoResultFound

from src.models.user import Role
from src.modules.users.repositories.base import BaseSQLRepository
from src.modules.users.schemas.role import RoleUpdateSchema


class BaseRoleRepository(ABC):
    """
    Абстрактный базовый класс для репозитория ролей, определяющий CRUD операции.
    """


class RoleRepository(BaseRoleRepository, BaseSQLRepository):

    async def get_role_all(self) -> list[Role]:
        """ Получает список всех ролей """
        query = select(Role).order_by(Role.name.asc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_role_by_id(self, role_id: UUID) -> Role:
        """ Получает роль по её ID """
        query = select(Role).where(Role.id == role_id)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def create(self, role: Role) -> None:
        """ Создаёт новую роль """
        self.session.add(role)

    async def update(self, role_id: UUID, body: RoleUpdateSchema) -> Role:
        """ Обновляет роль по её ID """
        update_data = {k: v for k, v in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound("Нет данных для обновления")

        stmt = (
            update(Role)
            .where(Role.id == role_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_role_by_id(role_id)

    async def delete(self, role_id: UUID) -> None:
        """ Удаляет роль по её ID """
        result = await self.get_role_by_id(role_id)
        if not result:
            raise NoResultFound(f"Роль с ID {role_id} не найдена")

        await self.session.delete(result)
