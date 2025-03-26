import os
from uuid import UUID
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.patient import RawImage
from src.modules.patients.schemas.raw_image import RawImageSchema, RawImageUpdateSchema, RawImageQueryParams


class RawImageRepository:
    """
    Репозиторий для работы с исходными изображениями
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, params: RawImageQueryParams) -> List[RawImageSchema]:
        """ Возвращает список исходных изображений """
        query = select(RawImage)

        if params.session:
            query = query.where(RawImage.session_id == params.session)

        query = query.limit(params.limit).offset(params.offset * params.limit)

        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_by_id(self, image_id: UUID) -> RawImageSchema:
        """ Возвращает данные исходного изображения по его ID """
        query = select(RawImage).where(RawImage.id == image_id)
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def bulk_create(self, images: list[RawImage]) -> None:
        """ Загружает новые исходные изображения """
        self.session.add_all(images)

    async def update(self, image_id: UUID, body: RawImageUpdateSchema) -> Optional[RawImageSchema]:
        """ Обновляет данные исходного изображения по его ID """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound(f"Нет данных для обновления")

        stmt = (
            update(RawImage)
            .filter_by(id=image_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(image_id)

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

    async def bulk_delete(self, ids: list[UUID]) -> None:
        """ Удаляет исходные изображения по списку ID """
        stmt = delete(RawImage).where(RawImage.id.in_(ids))
        await self.session.execute(stmt)

    async def bulk_delete(self, ids: list[UUID]) -> None:
        """ Удаляет исходные изображения по списку ID вместе с файлами """
        query = select(RawImage).where(RawImage.id.in_(ids))
        result = await self.session.execute(query)
        images = result.scalars().all()

        for img in images:
            try:
                if os.path.exists(img.file_path):
                    os.remove(img.file_path)
            except Exception as e:
                print(f"[WARN] Ошибка при удалении файла {img.file_path}: {e}")

            await self.session.delete(img)
