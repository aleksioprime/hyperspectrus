from uuid import UUID
from typing import List
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.repositories.uow import UnitOfWork
from src.schemas.role import RoleSchema, RoleUpdateSchema
from src.exceptions.crud import CreateError, UpdateError, DeleteError, NotFoundError

class RoleService:
    """ Сервис для управления ролями. """
    def __init__(self, uow: UnitOfWork, redis: Redis):
        self.uow = uow
        self.redis = redis

    async def create(self, body: RoleSchema) -> RoleSchema:
        """ Создаёт новую роль """
        async with self.uow:
            try:
                role = await self.uow.role.create(body)
            except IntegrityError as exc:
                raise CreateError(message='Role already exists!') from exc

        return role

    async def get_role_all(self) -> List[RoleSchema]:
        """ Выдаёт список всех ролей """
        async with self.uow:
            roles = await self.uow.role.get_role_all()
            return roles

        return roles

    async def update(self, role_id: UUID, body: RoleUpdateSchema) -> RoleSchema:
        """ Обновляет информацию о роли по её ID """
        async with self.uow:
            try:
                role = await self.uow.role.update(role_id, body)
            except NoResultFound as exc:
                raise UpdateError(f"Role with id {role_id} not found.") from exc
        return role

    async def delete(self, role_id: UUID) -> None:
        """ Удаляет роль по её ID """
        async with self.uow:
            try:
                await self.uow.role.delete(role_id)
            except NoResultFound as exc:
                raise DeleteError(f"Role with id {role_id} not found") from exc
            except Exception as e:
                raise DeleteError(f"Failed to delete role with id {role_id}. Error: {str(e)}") from e