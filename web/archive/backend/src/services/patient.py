from uuid import UUID
from typing import List
from redis.asyncio import Redis

from src.schemas.patient import PatientSchema, PatientCreateSchema, PatientUpdateSchema, PatientDetailSchema, PatientQueryParams
from src.repositories.patient import PatientRepository

class PatientService:
    """ Сервис для управления пациентами """
    def __init__(self, repository: PatientRepository):
        self.repository = repository

    async def get_all(self, params: PatientQueryParams) -> List[PatientSchema]:
        """ Выдаёт список пациентов """
        patients = await self.repository.get_all(params)
        return patients

    async def get_by_id(self, patient_id: UUID) -> PatientDetailSchema:
        """ Выдаёт пациента по его ID """
        patient = await self.repository.get_by_id(patient_id)
        return patient

    async def create(self, body: PatientCreateSchema) -> PatientSchema:
        """ Создаёт нового пациента """
        patient = await self.repository.create(body)
        return patient

    async def update(self, patient_id: UUID, body: PatientUpdateSchema) -> PatientSchema:
        """ Обновляет информацию о пациенте по его ID """
        patient = await self.repository.update(patient_id, body)
        return patient

    async def delete(self, patient_id: UUID) -> None:
        """ Удаляет пациента по его ID """
        await self.repository.delete(patient_id)