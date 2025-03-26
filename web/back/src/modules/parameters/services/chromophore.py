from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions.base import BaseException
from src.models.parameter import Chromophore
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.schemas.chromophore import ChromophoreSchema, ChromophoreUpdateSchema


class ChromophoreService:
    """
    Сервис для управления хромофорами
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all(self) -> List[ChromophoreSchema]:
        """
        Выдаёт список всех хромофор
        """
        async with self.uow:
            chromophores = await self.uow.chromophore.get_all()

        return chromophores

    async def create(self, body: ChromophoreUpdateSchema) -> ChromophoreSchema:
        """
        Создаёт новый хромофор
        """
        async with self.uow:
            try:
                chromophore = Chromophore(
                    name=body.name,
                    symbol=body.symbol,
                )
                await self.uow.chromophore.create(chromophore)
            except IntegrityError as exc:
                raise BaseException("Хромофор уже существует") from exc

        return chromophore

    async def update(self, chromophore_id: UUID, body: ChromophoreUpdateSchema) -> ChromophoreSchema:
        """
        Обновляет хромофор по его ID
        """
        async with self.uow:
            try:
                chromophore = await self.uow.chromophore.update(chromophore_id, body)
            except NoResultFound as exc:
                raise BaseException(f"Хромофор с ID {chromophore_id} не найден") from exc
        return chromophore

    async def delete(self, chromophore_id: UUID) -> None:
        """
        Удаляет хромофор по его ID
        """
        async with self.uow:
            try:
                await self.uow.chromophore.delete(chromophore_id)
            except NoResultFound as exc:
                raise BaseException(f"Хромофор с ID {chromophore_id} не найден") from exc