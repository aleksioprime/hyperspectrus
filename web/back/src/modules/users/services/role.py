from uuid import UUID
from typing import List

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from src.exceptions.base import BaseException
from src.models.user import Role
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.schemas.role import RoleSchema, RoleUpdateSchema


class RoleService:
    """
    Сервис для управления ролями
    """
    def __init__(self, uow: UnitOfWork, redis: Redis):
        self.uow = uow
        self.redis = redis

    async def get_all(self) -> List[RoleSchema]:
        """
        Выдаёт список всех ролей
        """
        async with self.uow:
            roles = await self.uow.role.get_role_all()

        return roles

    async def create(self, body: RoleUpdateSchema) -> RoleSchema:
        """
        Создаёт новую роль
        """
        async with self.uow:
            try:
                role = Role(
                    name=body.name,
                    description=body.description,
                )
                await self.uow.role.create(role)
            except IntegrityError as exc:
                raise BaseException("Роль уже существует") from exc

        return role

    async def update(self, role_id: UUID, body: RoleUpdateSchema) -> RoleSchema:
        """
        Обновляет информацию о роли по её ID
        """
        async with self.uow:
            try:
                role = await self.uow.role.update(role_id, body)
            except NoResultFound as exc:
                raise BaseException(f"Роль с ID {role_id} не найдена") from exc
        return role

    async def delete(self, role_id: UUID) -> None:
        """
        Удаляет роль по её ID
        """
        async with self.uow:
            try:
                await self.uow.role.delete(role_id)
            except NoResultFound as exc:
                raise BaseException(f"Роль с ID {role_id} не найдена") from exc