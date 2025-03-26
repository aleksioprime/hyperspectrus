from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions.base import BaseException
from src.models.parameter import Spectrum
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.schemas.spectrum import SpectrumSchema, SpectrumUpdateSchema, SpectrumQueryParams


class SpectrumService:
    """
    Сервис для управления спектрами
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all(self, params: SpectrumQueryParams) -> List[SpectrumSchema]:
        """
        Выдаёт список всех спектров
        """
        async with self.uow:
            spectrums = await self.uow.spectrum.get_all(params)

        return spectrums

    async def create(self, body: SpectrumUpdateSchema) -> SpectrumSchema:
        """
        Создаёт новый спектр
        """
        async with self.uow:
            try:
                spectrum = Spectrum(
                    wavelength=body.wavelength,
                    device_id=body.device_id,
                )
                await self.uow.spectrum.create(spectrum)
            except IntegrityError as exc:
                raise BaseException("Спектр уже существует") from exc

        return spectrum

    async def update(self, spectrum_id: UUID, body: SpectrumUpdateSchema) -> SpectrumSchema:
        """
        Обновляет информацию о спектре по его ID
        """
        async with self.uow:
            try:
                spectrum = await self.uow.spectrum.update(spectrum_id, body)
            except NoResultFound as exc:
                raise BaseException(f"Спектр с ID {spectrum_id} не найден") from exc
        return spectrum

    async def delete(self, spectrum_id: UUID) -> None:
        """
        Удаляет спектр по его ID
        """
        async with self.uow:
            try:
                await self.uow.spectrum.delete(spectrum_id)
            except NoResultFound as exc:
                raise BaseException(f"Спектр с ID {spectrum_id} не найден") from exc