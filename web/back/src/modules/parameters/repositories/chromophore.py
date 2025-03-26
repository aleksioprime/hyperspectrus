from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.parameter import Chromophore, Spectrum, OverlapCoefficient
from src.modules.parameters.schemas.chromophore import ChromophoreUpdateSchema


class ChromophoreRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Chromophore]:
        """ Получает список всех хромофоров """
        query = select(Chromophore)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, chromophore_id: UUID) -> Chromophore:
        """ Получает хромофор по его ID """
        query = select(Chromophore).where(Chromophore.id == chromophore_id)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def create(self, chromophore: Chromophore) -> None:
        """ Создаёт новый хромофор """
        self.session.add(chromophore)

    async def update(self, chromophore_id: UUID, body: ChromophoreUpdateSchema) -> Chromophore:
        """ Обновляет хромофор по его ID """
        update_data = {k: v for k, v in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound("Нет данных для обновления")

        stmt = (
            update(Chromophore)
            .where(Chromophore.id == chromophore_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(chromophore_id)

    async def delete(self, chromophore_id: UUID) -> None:
        """ Удаляет хромофор по его ID """
        result = await self.get_by_id(chromophore_id)
        if not result:
            raise NoResultFound(f"Хромофор с ID {chromophore_id} не найден")

        await self.session.delete(result)
