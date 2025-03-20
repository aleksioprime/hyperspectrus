from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import update, delete, insert, select
from sqlalchemy.exc import NoResultFound

from src.models.role import Role
from src.repositories.base import BaseSQLRepository
from src.schemas.role import RoleUpdateSchema


class BaseRoleRepository(ABC):
    """
    Абстрактный базовый класс для репозитория ролей, определяющий CRUD операции.
    """


class RoleRepository(BaseRoleRepository, BaseSQLRepository):

    async def get_role_all(self) -> list[Role]:
        """
        Получает список всех ролей
        """
        query = select(Role)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_role_by_id(self, role_id: UUID) -> Role:
        query = select(Role).where(Role.id == role_id)
        result = await self.session.execute(query)
        role = result.scalars().one_or_none()
        if not role:
            raise NoResultFound(f"Роль с ID {role_id} не найдена.")
        return role

    async def create(self, body: RoleUpdateSchema) -> Role:
        """
        Создаёт новую роль
        """
        role = Role(
            name=body.name,
            description=body.description,
        )

        self.session.add(role)
        await self.session.flush()

        return role

    async def update(self, role_id: UUID, body: RoleUpdateSchema) -> Role:
        """
        Обновляет данные роли по её ID
        """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound(f"Нет данных")

        query = (
            update(Role)
            .filter_by(id=role_id)
            .values(**update_data)
        )
        await self.session.execute(query)

        updated_role = await self.get_role_by_id(role_id)

        return updated_role

    async def delete(self, role_id: UUID) -> None:
        """
        Удаляет роль по её ID
        """
        role = await self.get_role_by_id(role_id)

        await self.session.delete(role)
        await self.session.flush()
