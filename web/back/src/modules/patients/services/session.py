from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError

from src.exceptions.base import BaseException
from src.models.patient import Session
from src.modules.patients.schemas.session import (
    SessionSchema, SessionCreateSchema, SessionUpdateSchema, SessionDetailSchema, SessionQueryParams,)
from src.modules.patients.repositories.uow import UnitOfWork


class SessionService:
    """ Сервис для управления сеансами пациентов """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all(self, params: SessionQueryParams) -> List[SessionSchema]:
        """
        Выдаёт список сеансов пациентов
        """
        async with self.uow:
            sessions = await self.uow.session_repo.get_all(params)

        return sessions

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

    async def create(self, body: SessionCreateSchema, user_id: UUID, patient_id: UUID) -> SessionSchema:
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

    async def update(self, body: SessionUpdateSchema, patient_id: UUID, session_id: UUID) -> SessionSchema:
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
            session = await self._get_session_checked(session_id, patient_id)
            await self.uow.session_repo.delete(session_id)

    async def _get_session_checked(self, session_id: UUID, patient_id: UUID) -> Session:
        session = await self.uow.session_repo.get_by_id(session_id)
        if not session:
            raise BaseException("Сеанс не найден")
        if session.patient_id != patient_id:
            raise BaseException("Сеанс не принадлежит указанному пациенту")
        return session