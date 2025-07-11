import os
from uuid import UUID
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, delete
from sqlalchemy.exc import NoResultFound

from src.models.patient import RawImage
from src.modules.patients.schemas.raw_image import RawImageSchema


class RawImageRepository:
    """
    Репозиторий для работы с исходными изображениями
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, image_id: UUID) -> RawImageSchema:
        """ Возвращает данные исходного изображения по его ID """
        query = select(RawImage).where(RawImage.id == image_id)
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def bulk_create(self, images: list[RawImage]) -> None:
        """ Загружает новые исходные изображения """
        self.session.add_all(images)

    async def delete(self, image_id: UUID) -> bool:
        """ Удаляет исходное изображение и его файл с диска """
        raw_image = await self.get_by_id(image_id)
        if not raw_image:
            raise NoResultFound(f"Исходное изображение с ID {image_id} не найдено")

        # Удаление файла с диска
        try:
            if os.path.exists(raw_image.file_path):
                os.remove(raw_image.file_path)
        except Exception as e:
            # Логируем, но не блокируем удаление из БД
            print(f"[WARN] Не удалось удалить файл: {raw_image.file_path} — {e}")

        # Удаление из БД
        await self.session.delete(raw_image)

    async def get_by_ids(self, ids: List[UUID]) -> list[RawImage]:
        """ Возвращает список изображений по списку UUID """
        if not ids:
            return []
        query = select(RawImage).where(RawImage.id.in_(ids))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def bulk_delete(self, ids: list[UUID]) -> None:
        """ Удаляет исходные изображения по списку ID """
        stmt = delete(RawImage).where(RawImage.id.in_(ids))
        await self.session.execute(stmt)

    async def get_session_id_by_image_id(self, image_id: UUID) -> Optional[UUID]:
        query = select(RawImage.session_id).where(RawImage.id == image_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_session_ids_by_image_ids(self, ids: list[UUID]) -> set[UUID]:
        if not ids:
            return set()
        query = select(RawImage.session_id).where(RawImage.id.in_(ids))
        result = await self.session.execute(query)
        return set(result.scalars().all())
