from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions.base import BaseException
from src.models.parameter import OverlapCoefficient
from src.modules.parameters.repositories.uow import UnitOfWork
from src.modules.parameters.schemas.overlap import OverlapCoefficientSchema, OverlapCoefficientUpdateSchema


class OverlapCoefficientService:
    """
    Сервис для управления коэффициентами перекрытия
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create(self, body: OverlapCoefficientUpdateSchema) -> OverlapCoefficientSchema:
        """
        Создаёт новый коэффициент перекрытия
        """
        async with self.uow:
            try:
                overlap_coefficient = OverlapCoefficient(
                    spectrum_id=body.spectrum_id,
                    chromophore_id=body.chromophore_id,
                    coefficient=body.coefficient,
                )
                await self.uow.overlap.create(overlap_coefficient)
            except IntegrityError as exc:
                raise BaseException("Коэффициент перекрытия уже существует") from exc

        return overlap_coefficient

    async def update(self, overlap_coefficient_id: UUID, body: OverlapCoefficientUpdateSchema) -> OverlapCoefficientSchema:
        """
        Обновляет коэффициент перекрытия по его ID
        """
        async with self.uow:
            try:
                overlap_coefficient = await self.uow.overlap.update(overlap_coefficient_id, body)
            except NoResultFound as exc:
                raise BaseException(f"Коэффициент перекрытия с ID {overlap_coefficient_id} не найден") from exc
        return overlap_coefficient

    async def delete(self, overlap_coefficient_id: UUID) -> None:
        """
        Удаляет коэффициент перекрытия по его ID
        """
        async with self.uow:
            try:
                await self.uow.overlap.delete(overlap_coefficient_id)
            except NoResultFound as exc:
                raise BaseException(f"Коэффициент перекрытия с ID {overlap_coefficient_id} не найден") from exc