from uuid import UUID
from typing import List
import random

from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions.base import BaseException
from src.models.parameter import Device, OverlapCoefficient
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.schemas.device import DeviceSchema, DeviceUpdateSchema, DeviceDetailSchema
from src.modules.parameters.schemas.overlap import OverlapCoefficientUpdateSchema


class DeviceService:
    """
    Сервис для управления устройствами
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all(self) -> List[DeviceSchema]:
        """
        Выдаёт список всех устройств
        """
        async with self.uow:
            devices = await self.uow.device.get_all()

        return devices

    async def get_detail_by_id(self, device_id: UUID) -> DeviceDetailSchema:
        """
        Выдаёт детальную информацию об устройстве по его ID
        """
        async with self.uow:
            device = await self.uow.device.get_detail_by_id(device_id)

            device.spectra.sort(key=lambda s: s.wavelength if s.wavelength is not None else 0)

        return device

    async def create(self, body: DeviceUpdateSchema) -> DeviceSchema:
        """
        Создаёт новое устройство
        """
        async with self.uow:
            try:
                device = Device(
                    name=body.name,
                )
                await self.uow.device.create(device)
            except IntegrityError as exc:
                raise BaseException("Устройство уже существует") from exc

        return device

    async def update(self, device_id: UUID, body: DeviceUpdateSchema) -> DeviceSchema:
        """
        Обновляет информацию об устройстве по его ID
        """
        async with self.uow:
            try:
                device = await self.uow.device.update(device_id, body)
            except NoResultFound as exc:
                raise BaseException(f"Устройство с ID {device_id} не найдено") from exc
        return device

    async def delete(self, device_id: UUID) -> None:
        """
        Удаляет устройство по его ID
        """
        async with self.uow:
            try:
                await self.uow.device.delete(device_id)
            except NoResultFound as exc:
                raise BaseException(f"Устройство с ID {device_id} не найдено") from exc

    async def fill_overlaps_random(self, device_id: UUID):
        """
        Заполнить все коэффициенты перекрытия устройства случайными числами (0...50000, 2 знака)
        """
        async with self.uow:
            device = await self.uow.device.get_detail_by_id(device_id)
            if not device:
                raise BaseException(f"Устройство с ID {device_id} не найдено")

            chromophores = await self.uow.chromophore.get_all()

            for spectrum in device.spectra:
                for chromophore in chromophores:
                    if chromophore.symbol.lower() == "bkg":
                        coefficient_value = 100.00
                    else:
                        coefficient_value = round(random.uniform(0, 50000), 2)
                    overlap = await self.uow.overlap.get_by_spec_and_chrom(
                        spectrum.id, chromophore.id
                    )
                    if overlap:
                        await self.uow.overlap.update(
                            overlap.id,
                            OverlapCoefficientUpdateSchema(coefficient=coefficient_value)
                        )
                    else:
                        await self.uow.overlap.create(
                            OverlapCoefficient(
                                spectrum_id=spectrum.id,
                                chromophore_id=chromophore.id,
                                coefficient=coefficient_value,
                            )
                        )