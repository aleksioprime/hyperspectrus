from uuid import UUID
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.constants.celery import CeleryStatus
from src.models.patient import Session, RawImage, ReconstructedImage
from src.modules.patients.schemas.session import SessionUpdateSchema


class SessionRepository:
    """
    Репозиторий для работы с сеансами
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, session_id: UUID) -> Session:
        """ Возвращает сеанс по его ID """
        query = select(Session).where(Session.id == session_id)
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def get_detail_by_id(self, session_id: UUID) -> Session:
        """ Возвращает сеанс по его ID """
        query = (
            select(Session)
            .options(
                joinedload(Session.patient),
                joinedload(Session.operator),
                joinedload(Session.device),
                joinedload(Session.raw_images)
                    .joinedload(RawImage.spectrum),
                joinedload(Session.reconstructed_images)
                    .joinedload(ReconstructedImage.chromophore),
                joinedload(Session.result),
            )
            .where(Session.id == session_id)
        )
        result = await self.session.execute(query)
        return result.unique().scalars().one_or_none()

    async def create(self, session: Session) -> Session:
        """ Создаёт новый сеанс пациента """
        self.session.add(session)
        await self.session.flush()
        return await self.get_detail_by_id(session.id)

    async def update(self, session_id: UUID, body: SessionUpdateSchema) -> Optional[Session]:
        """ Обновляет сеанс по его ID """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound(f"Нет данных для обновления")

        stmt = (
            update(Session)
            .filter_by(id=session_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_detail_by_id(session_id)

    async def delete(self, session_id: UUID) -> bool:
        """ Удаляет сеанс по его ID """
        result = await self.get_by_id(session_id)
        if not result:
            raise NoResultFound(f"Сеанс с ID {session_id} не найден")

        await self.session.delete(result)

    async def set_processing_task_id(self, session_id: UUID, task_id: str) -> None:
        """Сохраняет ID задачи в указанный сеанс"""
        stmt = (
            update(Session)
            .where(Session.id == session_id)
                .values(
                processing_task_id=task_id,
                processing_status=CeleryStatus.PENDING.value
            )
        )
        await self.session.execute(stmt)

    async def clear_processing_task_id(self, session_id: UUID) -> None:
        """
        Очищает ID задачи для указанного сеанса
        """
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(processing_task_id=None)
        )
        await self.session.execute(stmt)

    async def get_processing_task_id(self, session_id: UUID) -> str | None:
        """Получает ID задачи указанного сеанса"""
        query = select(Session.processing_task_id).where(Session.id == session_id)
        result = await self.session.execute(query)
        row = result.first()
        return row[0] if row else None
