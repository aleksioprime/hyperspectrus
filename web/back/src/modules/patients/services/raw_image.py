from uuid import UUID
from typing import List
import os
import uuid

from fastapi import UploadFile

from src.exceptions.base import BaseException
from src.models.patient import RawImage
from src.modules.patients.schemas.raw_image import (
    RawImageSchema, RawImageUpdateSchema, RawImageQueryParams)
from src.modules.patients.repositories.uow import UnitOfWork


class RawImageService:
    """ Сервис для управления исходными изображениями """
    def __init__(self, uow: UnitOfWork, media_root: str = "./media/raw_images"):
        self.uow = uow
        self.media_root = media_root

    async def get_all(self, params: RawImageQueryParams) -> List[RawImageSchema]:
        """
        Выдаёт список исходных изображений
        """
        async with self.uow:
            raw_images = await self.uow.raw_image.get_all(params)

        return raw_images

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

        os.makedirs(f"{self.media_root}/{session_id}", exist_ok=True)

        raw_images: list[RawImage] = []

        for file, spectrum_id in zip(files, spectrum_ids):
            file_ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{file_ext}"
            save_path = os.path.join(self.media_root, str(session_id), filename)

            # Сохраняем файл
            with open(save_path, "wb") as f:
                f.write(await file.read())

            # Запись в БД
            raw_images.append(RawImage(
                session_id=session_id,
                spectrum_id=spectrum_id,
                file_path=save_path,
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
        Удаляет исходное изображение сессии по его ID
        """
        async with self.uow:
            await self.uow.raw_image.delete(raw_image_id)

    async def bulk_delete(self, ids: list[UUID]) -> None:
        """
        Удаляет исходные изображения сессии по списку ID
        """
        async with self.uow:
            await self.uow.raw_image.bulk_delete(ids)