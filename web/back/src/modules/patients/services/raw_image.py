from uuid import UUID
from typing import List
import os
import uuid

from fastapi import UploadFile

from src.core.config import settings
from src.exceptions.base import BaseException
from src.models.patient import RawImage
from src.modules.patients.schemas.raw_image import RawImageSchema
from src.modules.patients.repositories.uow import UnitOfWork


class RawImageService:
    """ Сервис для управления исходными изображениями """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def upload_files(self, session_id: UUID, spectrum_ids: List[UUID], files: List[UploadFile]) -> List[RawImageSchema]:
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

    async def delete(self, raw_image_id: UUID) -> None:
        """
        Удаляет исходное изображение сессии по его ID с файлом
        """
        async with self.uow:
            raw_image = await self.uow.raw_image.get_by_id(raw_image_id)
            if not raw_image:
                return

            relative_path = raw_image.file_path.removeprefix(settings.media.raw_images_url).lstrip("/")
            abs_path = os.path.join(settings.media.raw_images_path, relative_path)

            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                except Exception as e:
                    raise BaseException(f"Ошибка удаления файла: {e}")

            session_id = await self.uow.raw_image.get_session_id_by_image_id(raw_image_id)

            await self.uow.raw_image.delete(raw_image_id)

            return session_id

    async def bulk_delete(self, ids: list[UUID]) -> set[UUID]:
        """
        Удаляет исходные изображения сессии по списку ID c файлами
        """
        async with self.uow:
            images = await self.uow.raw_image.get_by_ids(ids)
            for img in images:
                relative_path = img.file_path.removeprefix(settings.media.raw_images_url).lstrip("/")
                abs_path = os.path.join(settings.media.raw_images_path, relative_path)
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                    except Exception as e:
                        raise BaseException(f"Ошибка удаления файла: {e}")

            session_ids = await self.uow.raw_image.get_session_ids_by_image_ids(ids)

            await self.uow.raw_image.bulk_delete(ids)

            return session_ids