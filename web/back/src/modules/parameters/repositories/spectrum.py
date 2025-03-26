from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.exc import NoResultFound

from src.models.parameter import Spectrum
from src.modules.parameters.schemas.spectrum import SpectrumUpdateSchema, SpectrumQueryParams


class SpectrumRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, params: SpectrumQueryParams) -> list[Spectrum]:
        """ Получает список всех cпектров """
        query = select(Spectrum)

        if params.device:
            query = query.where(Spectrum.device_id == params.device)

        query = query.limit(params.limit).offset(params.offset * params.limit)

        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_by_id(self, spectrum_id: UUID) -> Spectrum:
        """ Получает спектр по его ID """
        query = select(Spectrum).where(Spectrum.id == spectrum_id)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def create(self, spectrum: Spectrum) -> None:
        """ Создаёт новый спектр """
        self.session.add(spectrum)

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
        spectrum = await self.get_by_id(spectrum_id)
        if not spectrum:
            raise NoResultFound(f"Спектр с ID {spectrum_id} не найден")

        if spectrum:
            await self.session.delete(spectrum)
