from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from uuid import UUID
from typing import List, Optional

from src.models.patient import Patient
from src.modules.patients.schemas.patient import PatientSchema, PatientCreateSchema, PatientUpdateSchema, PatientDetailSchema, PatientQueryParams
from src.exceptions.base import BaseException


class PatientRepository:
    """
    Репозиторий для работы с пациентами
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, params: PatientQueryParams) -> List[PatientSchema]:
        """ Возвращает список пациентов """
        query = select(Patient)

        if params.organization:
            query = query.where(Patient.organization_id == params.organization)

        query = query.limit(params.limit).offset(params.offset * params.limit)

        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_by_id(self, patient_id: UUID) -> PatientDetailSchema:
        """ Возвращает пациента по его ID """
        query = select(Patient).where(Patient.id == patient_id)
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def create(self, patient: Patient) -> PatientSchema:
        """ Создаёт нового пациента """
        self.session.add(patient)

    async def update(self, patient_id: UUID, body: PatientUpdateSchema) -> Optional[PatientSchema]:
        """ Обновляет пациента по его ID """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound(f"Нет данных для обновления")

        stmt = (
            update(Patient)
            .filter_by(id=patient_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(patient_id)

    async def delete(self, patient_id: UUID) -> bool:
        """ Удаляет пациента по его ID """
        patient = await self.get_by_id(patient_id)
        if not patient:
            raise NoResultFound(f"Пациент с ID {patient_id} не найден")

        await self.session.delete(patient)
