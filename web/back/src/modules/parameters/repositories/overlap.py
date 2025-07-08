from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.parameter import OverlapCoefficient
from src.modules.parameters.schemas.overlap import OverlapCoefficientUpdateSchema


class OverlapCoefficientRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, overlap_coefficient_id: UUID) -> OverlapCoefficient:
        """ Получает коэффициент перекрытия по его ID """
        query = select(OverlapCoefficient).where(OverlapCoefficient.id == overlap_coefficient_id)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def create(self, overlap_coefficient: OverlapCoefficient) -> None:
        """ Создаёт новый коэффициент перекрытия """
        self.session.add(overlap_coefficient)

    async def update(self, overlap_coefficient_id: UUID, body: OverlapCoefficientUpdateSchema) -> OverlapCoefficient:
        """ Обновляет коэффициент перекрытия по его ID """
        update_data = {k: v for k, v in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound("Нет данных для обновления")

        stmt = (
            update(OverlapCoefficient)
            .where(OverlapCoefficient.id == overlap_coefficient_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(overlap_coefficient_id)

    async def delete(self, overlap_coefficient_id: UUID) -> None:
        """ Удаляет коэффициент перекрытия по его ID """
        result = await self.get_by_id(overlap_coefficient_id)
        if not result:
            raise NoResultFound(f"Хромофор с ID {overlap_coefficient_id} не найден")

        await self.session.delete(result)

    async def get_by_spec_and_chrom(self, spectrum_id: UUID, chromophore_id: UUID) -> OverlapCoefficient | None:
        """ Получить все коэффициенты по спектру и хромофору """
        query = select(OverlapCoefficient).where(
            OverlapCoefficient.spectrum_id == spectrum_id,
            OverlapCoefficient.chromophore_id == chromophore_id
        )
        result = await self.session.execute(query)
        return result.scalars().one_or_none()
