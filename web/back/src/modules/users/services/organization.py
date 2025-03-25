from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions.base import BaseException
from src.models.user import Organization
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.schemas.organization import OrganizationSchema, OrganizationUpdateSchema


class OrganizationService:
    """
    Сервис для управления организациями
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all(self) -> List[OrganizationSchema]:
        """
        Выдаёт список всех организаций
        """
        async with self.uow:
            organizations = await self.uow.organization.get_organization_all()

        return organizations

    async def create(self, body: OrganizationUpdateSchema) -> OrganizationSchema:
        """
        Создаёт новую организацию
        """
        async with self.uow:
            try:
                organization = Organization(
                    name=body.name,
                    description=body.description,
                )
                await self.uow.organization.create(organization)
            except IntegrityError as exc:
                raise BaseException("Организация уже существует") from exc

        return organization

    async def update(self, organization_id: UUID, body: OrganizationUpdateSchema) -> OrganizationSchema:
        """
        Обновляет информацию об организации по её ID
        """
        async with self.uow:
            try:
                organization = await self.uow.organization.update(organization_id, body)
            except NoResultFound as exc:
                raise BaseException(f"Организация с ID {organization_id} не найдена") from exc
        return organization

    async def delete(self, organization_id: UUID) -> None:
        """
        Удаляет организацию по её ID
        """
        async with self.uow:
            try:
                await self.uow.organization.delete(organization_id)
            except NoResultFound as exc:
                raise BaseException(f"Организация с ID {organization_id} не найдена") from exc