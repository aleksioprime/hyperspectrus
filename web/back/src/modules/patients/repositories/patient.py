from uuid import UUID
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from src.models.patient import Patient, Session
from src.modules.patients.schemas.patient import PatientSchema, PatientUpdateSchema, PatientDetailSchema, PatientQueryParams


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

    async def get_all_with_count(self, params: PatientQueryParams) -> tuple[list[PatientSchema], int]:
        """ Возвращает постраничный список пациентов и их общее количество """
        query = select(Patient)
        if params.organization:
            query = query.where(Patient.organization_id == params.organization)

        total_query = select(func.count()).select_from(query.subquery())

        paginated_query = query.limit(params.limit).offset(params.offset * params.limit)

        total_result = await self.session.execute(total_query)
        result = await self.session.execute(paginated_query)

        total = total_result.scalar()
        items = result.scalars().unique().all()

        return items, total

    async def get_by_id(self, patient_id: UUID) -> PatientDetailSchema:
        """ Возвращает пациента по его ID """
        query = select(Patient).where(Patient.id == patient_id)
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def get_with_sessions_by_id(self, patient_id: UUID) -> Optional[Patient]:
        """ Возвращает пациента по его ID с сессиями """
        query = (
            select(Patient)
            .options(
                selectinload(Patient.sessions)
                .joinedload(Session.device),
                selectinload(Patient.sessions)
                .joinedload(Session.operator),
            )
            .where(Patient.id == patient_id)
        )
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
        result = await self.get_by_id(patient_id)
        if not result:
            raise NoResultFound(f"Пациент с ID {patient_id} не найден")

        await self.session.delete(result)
