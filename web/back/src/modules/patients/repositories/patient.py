from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from uuid import UUID
from typing import List, Optional

from src.models.patient import Patient
from src.schemas.patient import PatientSchema, PatientCreateSchema, PatientUpdateSchema, PatientDetailSchema, PatientQueryParams
from src.exceptions.patient import PatientException


class PatientRepository:
    """
    Репозиторий для работы с пациентами
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, params: PatientQueryParams) -> List[PatientSchema]:
        """
        Возвращает список пациентов по ID пользователя
        """
        try:
            query = select(Patient)

            if params.organization:
                query = query.where(Patient.organization_id == params.organization)

            query = query.limit(params.limit).offset(params.offset * params.limit)

            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise PatientException("Ошибка получения пациентов пользователя", str(e))

    async def get_by_id(self, patient_id: UUID) -> PatientDetailSchema:
        """
        Возвращает пациента по его ID
        """
        try:
            query = select(Patient).where(Patient.id == patient_id)
            result = await self.session.execute(query)
            patient = result.scalars().unique().one_or_none()

            if not patient:
                raise NoResultFound(f"Пациент с ID {patient_id} не найден")

            return patient
        except SQLAlchemyError as e:
            raise PatientException(f"Ошибка получения пациента: {str(e)}")

    async def create(self, body: PatientCreateSchema) -> PatientSchema:
        """
        Создаёт нового пациента
        """
        try:
            new_patient = Patient(
                organization_id=body.organization_id,
                name=body.name,
                birth_date=body.birth_date,
                notes=body.notes
                )
            self.session.add(new_patient)
            await self.session.commit()
            await self.session.refresh(new_patient)
            return new_patient
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PatientException(f"Ошибка создания пациента: {str(e)}")

    async def update(self, patient_id: UUID, body: PatientUpdateSchema) -> Optional[PatientSchema]:
        """
        Обновляет пациента по его ID
        """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound(f"Нет данных для обновления")

        try:
            query = (
                update(Patient)
                .filter_by(id=patient_id)
                .values(**update_data)
                .execution_options(synchronize_session="fetch")
            )
            await self.session.execute(query)
            await self.session.commit()

            updated_patient = await self.get_by_id(patient_id)

            return updated_patient
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PatientException(f"Ошибка редактирования пациента: {str(e)}")

    async def delete(self, patient_id: UUID) -> bool:
        """
        Удаляет пациента по его ID
        """
        try:
            deleted_patient = await self.get_by_id(patient_id)

            await self.session.delete(deleted_patient)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PatientException(f"Ошибка удаления пациента: {str(e)}")
