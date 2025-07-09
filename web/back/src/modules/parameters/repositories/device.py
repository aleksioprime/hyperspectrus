from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.parameter import Device, Spectrum, OverlapCoefficient
from src.modules.parameters.schemas.device import DeviceUpdateSchema


class DeviceRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Device]:
        """ Получает список всех устройств """
        query = select(Device)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, device_id: UUID) -> Device:
        """ Получает устройство по его ID """
        query = select(Device).where(Device.id == device_id)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def get_detail_by_id(self, device_id: UUID) -> Device:
        """ Получает детальную информацию об устройстве по его ID """
        query = (
            select(Device)
            .options(
                joinedload(Device.spectra)
                .joinedload(Spectrum.overlaps)
                .joinedload(OverlapCoefficient.chromophore)
            )
            .where(Device.id == device_id)
        )
        result = await self.session.execute(query)
        return result.unique().scalars().one_or_none()

    async def create(self, device: Device) -> None:
        """ Создаёт новое устройство """
        self.session.add(device)

    async def update(self, device_id: UUID, body: DeviceUpdateSchema) -> Device:
        """ Обновляет устройство по его ID """
        update_data = {k: v for k, v in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound("Нет данных для обновления")

        stmt = (
            update(Device)
            .where(Device.id == device_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(device_id)

    async def delete(self, device_id: UUID) -> None:
        """ Удаляет устройство по его ID """
        result = await self.get_by_id(device_id)
        if not result:
            raise NoResultFound(f"Устройство с ID {device_id} не найдено")

        await self.session.delete(result)
