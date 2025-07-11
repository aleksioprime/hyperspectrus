from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError

from src.exceptions.base import BaseException
from src.models.patient import Session
from src.modules.patients.schemas.session import SessionCreateSchema, SessionUpdateSchema, SessionDetailSchema
from src.modules.patients.repositories.uow import UnitOfWork

from src.celery_app import celery_app
from src.constants.celery import CeleryStatus, CELERY_STATUS_MAP


class SessionService:
    """ Сервис для управления сеансами пациентов """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_detail_by_id(self, patient_id: UUID, session_id: UUID) -> SessionDetailSchema:
        """
        Выдаёт сеанс пациента по её ID
        """
        async with self.uow:
            session = await self.uow.session_repo.get_detail_by_id(session_id)

            if not session:
                raise BaseException(f"Сессия с ID {session_id} не найдена")

            if session.patient_id != patient_id:
                raise BaseException("Сессия не принадлежит указанному пациенту")

        return session

    async def create(self, body: SessionCreateSchema, user_id: UUID, patient_id: UUID) -> SessionDetailSchema:
        """
        Создаёт новый сеанс пациента
        """
        async with self.uow:
            try:
                session = Session(
                    patient_id=patient_id,
                    device_id=body.device_id,
                    operator_id=user_id,
                    notes=body.notes
                    )
                await self.uow.session_repo.create(session)
            except IntegrityError as e:
                raise BaseException("Сеанс уже существует") from e

        return session

    async def update(self, body: SessionUpdateSchema, patient_id: UUID, session_id: UUID) -> SessionDetailSchema:
        """
        Обновляет информацию о сеансе пациента по его ID
        """
        async with self.uow:
            session = await self._get_session_checked(session_id, patient_id)
            session = await self.uow.session_repo.update(session_id, body)

        return session

    async def delete(self, patient_id: UUID, session_id: UUID) -> None:
        """
        Удаляет сеанс по его ID
        """
        async with self.uow:
            await self._get_session_checked(session_id, patient_id)
            await self.uow.session_repo.delete(session_id)

    async def set_processing_task_id(self, session_id: UUID, task_id: str) -> None:
        """
        Записывает ID задачи обработки данных в указанный сеанс
        """
        async with self.uow:
            await self.uow.session_repo.set_processing_task_id(session_id, task_id)

    async def get_processing_status(self, patient_id: UUID, session_id: UUID) -> dict:
        async with self.uow:
            await self._get_session_checked(session_id, patient_id)

            task_id = await self.uow.session_repo.get_processing_task_id(session_id)

            if not task_id:
                return {
                    "task_id": None,
                    "celery_status": None,
                    "status": "NO_TASK",
                    "result": None,
                    "error": None,
                }

        result = celery_app.AsyncResult(task_id)
        celery_status = CeleryStatus(result.status) if result.status in CeleryStatus.__members__.values() else result.status

        return {
            "task_id": task_id,
            "celery_status": celery_status,
            "status": CELERY_STATUS_MAP.get(celery_status, celery_status),
            "result": result.result if celery_status == CeleryStatus.SUCCESS else None,
            "error": str(result.result) if celery_status == CeleryStatus.FAILURE else None,
        }

    async def clear_processing_task_id(self, patient_id: UUID, session_id: UUID) -> None:
        """
        Очищает ID задачи в указанном сеансе
        """
        async with self.uow:
            await self._get_session_checked(session_id, patient_id)
            await self.uow.session_repo.clear_processing_task_id(session_id)

    async def _get_session_checked(self, session_id: UUID, patient_id: UUID) -> Session:
        """
        Проверяет принадлежность сеанса указанному пользователю
        """
        session = await self.uow.session_repo.get_by_id(session_id)
        if not session:
            raise BaseException("Сеанс не найден")
        if session.patient_id != patient_id:
            raise BaseException("Сеанс не принадлежит указанному пациенту")
        return session