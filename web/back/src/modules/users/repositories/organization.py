from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import update, select
from sqlalchemy.exc import NoResultFound

from src.models.user import Organization
from src.modules.users.repositories.base import BaseSQLRepository
from src.modules.users.schemas.organization import OrganizationUpdateSchema


class BaseOrganizationRepository(ABC):
    """
    Абстрактный базовый класс для репозитория организаций, определяющий CRUD операции
    """


class OrganizationRepository(BaseOrganizationRepository, BaseSQLRepository):

    async def get_organization_all(self) -> list[Organization]:
        """ Получает список всех организаций """
        query = select(Organization)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_organization_by_id(self, organization_id: UUID) -> Organization:
        """ Получает организацию по её ID """
        query = select(Organization).where(Organization.id == organization_id)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def create(self, organization: Organization) -> None:
        """ Создаёт новую организацию """
        self.session.add(organization)

    async def update(self, organization_id: UUID, body: OrganizationUpdateSchema) -> Organization:
        """ Обновляет организацию по её ID """
        update_data = {k: v for k, v in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound("Нет данных для обновления")

        stmt = (
            update(Organization)
            .where(Organization.id == organization_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_organization_by_id(organization_id)

    async def delete(self, organization_id: UUID) -> None:
        """ Удаляет организацию по её ID """
        result = await self.get_organization_by_id(organization_id)
        if not result:
            raise NoResultFound(f"Организация с ID {organization_id} не найдена")

        await self.session.delete(result)
