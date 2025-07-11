from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from src.models.parameter import Spectrum
from src.modules.parameters.schemas.spectrum import SpectrumUpdateSchema


class SpectrumRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, device_id: UUID) -> list[Spectrum]:
        """ Получает список всех cпектров """
        query = (
            select(Spectrum)
            .where(Spectrum.device_id == device_id)
            .options(selectinload(Spectrum.overlaps))
            .order_by(Spectrum.wavelength.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_by_id(self, spectrum_id: UUID) -> Spectrum:
        """ Получает спектр по его ID """
        query = (
            select(Spectrum)
            .where(Spectrum.id == spectrum_id)
            .options(selectinload(Spectrum.overlaps))
        )
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def create(self, spectrum: Spectrum) -> None:
        """ Создаёт новый спектр """
        self.session.add(spectrum)
        await self.session.flush()
        return await self.get_by_id(spectrum.id)

    async def update(self, spectrum_id: UUID, body: SpectrumUpdateSchema) -> Spectrum:
        """ Обновляет спектр по его ID """
        update_data = {k: v for k, v in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound("Нет данных для обновления")

        stmt = (
            update(Spectrum)
            .where(Spectrum.id == spectrum_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(spectrum_id)

    async def delete(self, spectrum_id: UUID) -> None:
        """ Удаляет спектр по его ID """
        result = await self.get_by_id(spectrum_id)
        if not result:
            raise NoResultFound(f"Спектр с ID {spectrum_id} не найден")

        await self.session.delete(result)
