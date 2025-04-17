from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions.base import BaseException
from src.models.parameter import Spectrum
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.schemas.spectrum import SpectrumSchema, SpectrumUpdateSchema


class SpectrumService:
    """
    Сервис для управления спектрами
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all(self, device_id: UUID) -> List[SpectrumSchema]:
        """
        Выдаёт список всех спектров устройства по его ID
        """
        async with self.uow:
            spectrums = await self.uow.spectrum.get_all(device_id)

        return spectrums

    async def create(self, device_id: UUID, body: SpectrumUpdateSchema) -> SpectrumSchema:
        """
        Создаёт новый спектр устройства
        """
        async with self.uow:
            try:
                spectrum = Spectrum(
                    wavelength=body.wavelength,
                    device_id=device_id,
                )
                await self.uow.spectrum.create(spectrum)
            except IntegrityError as exc:
                raise BaseException("Спектр уже существует") from exc

        return spectrum

    async def update(self, device_id: UUID, spectrum_id: UUID, body: SpectrumUpdateSchema) -> SpectrumSchema:
        """
        Обновляет информацию о спектре устройства по его ID
        """
        async with self.uow:
            spectrum = await self._get_spectrum_checked(device_id, spectrum_id)
            spectrum = await self.uow.spectrum.update(spectrum_id, body)

        return spectrum

    async def delete(self, device_id: UUID, spectrum_id: UUID) -> None:
        """
        Удаляет спектр устройства по его ID
        """
        async with self.uow:
            spectrum = await self._get_spectrum_checked(device_id, spectrum_id)
            await self.uow.spectrum.delete(spectrum_id)

    async def _get_spectrum_checked(self, device_id: UUID, spectrum_id: UUID) -> Spectrum:
        spectrum = await self.uow.spectrum.get_by_id(spectrum_id)
        if not spectrum:
            raise BaseException("Спектр не найден")
        if spectrum.device_id != device_id:
            raise BaseException("Спектр не принадлежит указанному устройству")
        return spectrum