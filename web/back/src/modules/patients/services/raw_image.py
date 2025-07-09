from uuid import UUID
from typing import List
import os
import uuid

from fastapi import UploadFile

from src.core.config import settings
from src.exceptions.base import BaseException
from src.models.patient import RawImage
from src.modules.patients.schemas.raw_image import (
    RawImageSchema, RawImageUpdateSchema)
from src.modules.patients.repositories.uow import UnitOfWork


class RawImageService:
    """ Сервис для управления исходными изображениями """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def upload_files(
        self,
        session_id: UUID,
        spectrum_ids: List[UUID],
        files: List[UploadFile],
    ) -> List[RawImageSchema]:
        """
        Сохраняет файлы фотографий и информацию о них в БД
        """
        if len(files) != len(spectrum_ids):
            raise BaseException("Количество файлов и спектров должно совпадать")

        os.makedirs(f"{settings.media.raw_images_path}/{session_id}", exist_ok=True)

        raw_images: list[RawImage] = []

        for file, spectrum_id in zip(files, spectrum_ids):
            file_ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{file_ext}"
            path = f"{settings.media.raw_images_url}/{session_id}/{filename}"
            save_path = os.path.join(settings.media.raw_images_path, str(session_id), filename)

            # Сохраняем файл
            with open(save_path, "wb") as f:
                f.write(await file.read())

            # Запись в БД
            raw_images.append(RawImage(
                session_id=session_id,
                spectrum_id=spectrum_id,
                file_path=path,
            ))

        async with self.uow:
            await self.uow.raw_image.bulk_create(raw_images)

        return raw_images

    async def update(self, raw_image_id: UUID, body: RawImageUpdateSchema) -> RawImageSchema:
        """
        Обновляет информацию об исходном изображении сессии по его ID
        """
        async with self.uow:
            raw_image = await self.uow.raw_image.update(raw_image_id, body)

        return raw_image

    async def delete(self, raw_image_id: UUID) -> None:
        """
        Удаляет исходное изображение сессии по его ID с файлом
        """
        async with self.uow:
            raw_image = await self.uow.raw_image.get_by_id(raw_image_id)
            if not raw_image:
                return

            abs_path = os.path.join(settings.media.raw_images_path, raw_image.file_path.lstrip(settings.media.raw_images_url))
            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                except Exception as e:
                    raise BaseException(f"Ошибка удаления файла: {e}")

            await self.uow.raw_image.delete(raw_image_id)

    async def bulk_delete(self, ids: list[UUID]) -> None:
        """
        Удаляет исходные изображения сессии по списку ID c файлами
        """
        async with self.uow:
            images = await self.uow.raw_image.get_by_ids(ids)
            for img in images:
                abs_path = os.path.join(settings.media.raw_images_path, img.file_path.lstrip(settings.media.raw_images_url))
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                    except Exception as e:
                        raise BaseException(f"Ошибка удаления файла: {e}")

            await self.uow.raw_image.bulk_delete(ids)