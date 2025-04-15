from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError

from src.core.schemas import PaginatedResponse
from src.exceptions.base import BaseException
from src.models.patient import Patient
from src.modules.patients.schemas.patient import (
    PatientSchema, PatientCreateSchema, PatientUpdateSchema, PatientDetailSchema, PatientQueryParams,)
from src.modules.patients.repositories.uow import UnitOfWork


class PatientService:
    """ Сервис для управления пациентами """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all(self, params: PatientQueryParams) -> List[PatientSchema]:
        """
        Выдаёт список пациентов
        """
        async with self.uow:
            patients, total = await self.uow.patient.get_all_with_count(params)

        return PaginatedResponse[PatientSchema](
            items=patients,
            total=total,
            limit=params.limit,
            offset=params.offset,
            has_next=(params.offset + 1) * params.limit < total,
            has_previous=params.offset > 0
        )

    async def get_by_id(self, patient_id: UUID) -> PatientDetailSchema:
        """
        Выдаёт пациента по его ID
        """
        async with self.uow:
            patient = await self.uow.patient.get_with_sessions_by_id(patient_id)

            if not patient:
                raise BaseException(f"Пациент с ID {patient_id} не найден")

        return patient

    async def create(self, body: PatientCreateSchema) -> PatientSchema:
        """
        Создаёт нового пациента
        """
        async with self.uow:
            try:
                patient = Patient(
                    organization_id=body.organization_id,
                    full_name=body.full_name,
                    birth_date=body.birth_date,
                    notes=body.notes
                    )
                await self.uow.patient.create(patient)
            except IntegrityError as e:
                raise BaseException("Пользователь уже существует") from e

        return patient

    async def update(self, patient_id: UUID, body: PatientUpdateSchema) -> PatientSchema:
        """
        Обновляет информацию о пациенте по его ID
        """
        async with self.uow:
            patient = await self.uow.patient.update(patient_id, body)

        return patient

    async def delete(self, patient_id: UUID) -> None:
        """
        Удаляет пациента по его ID
        """
        async with self.uow:
            await self.uow.patient.delete(patient_id)