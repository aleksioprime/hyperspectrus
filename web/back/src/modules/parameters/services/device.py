from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions.base import BaseException
from src.models.parameter import Device
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.schemas.device import DeviceSchema, DeviceUpdateSchema, DeviceDetailSchema


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