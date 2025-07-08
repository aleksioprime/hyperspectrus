import os
import shutil
import logging
from uuid import UUID

from fastapi import UploadFile, HTTPException
from sqlalchemy.exc import IntegrityError

from src.core.config import settings
from src.core.schemas import PaginatedResponse
from src.models.user import User
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.schemas.user import UserCreateSchema, UserUpdateSchema, UpdatePasswordUserSchema, UserSchema, UserQueryParams
from src.modules.users.serializers.user import BaseSerializer
from src.exceptions.base import BaseException

logger = logging.getLogger(__name__)


class UserService:

    def __init__(self, uow: UnitOfWork, serializer: BaseSerializer):
        self.uow = uow
        self.serializer = serializer

    async def get_user_all(self, params: UserQueryParams) -> PaginatedResponse[UserSchema]:
        """
        Выдаёт пагинированную информацию обо всех пользователях
        """
        async with self.uow:
            users, total = await self.uow.user.get_user_all(params)

        return PaginatedResponse[UserSchema](
                items=[self.serializer.serialize(user) for user in users],
                total=total,
                limit=params.limit,
                offset=params.offset,
                has_next=(params.offset + 1) * params.limit < total,
                has_previous=params.offset > 0
            )

    async def get_user_by_id(self, user_id: UUID) -> UserSchema:
        """
        Выдаёт информацию о пользователе по его ID
        """
        async with self.uow:
            user = await self.uow.user.get_user_by_id(user_id)
            if not user:
                raise BaseException(f"Пользователь с ID {user_id} не найден")
        return self.serializer.serialize(user)

    async def create(self, body: UserCreateSchema) -> User:
        """
        Создаёт пользователя
        """
        async with self.uow:
            try:
                user = User(
                    username=body.username,
                    password=body.password,
                    email=body.email,
                    first_name=body.first_name,
                    last_name=body.last_name,
                    organization_id=body.organization_id,
                    is_superuser=body.is_superuser,
                )
                await self.uow.user.create(user, role_ids=body.roles)
            except IntegrityError as e:
                raise BaseException("Пользователь уже существует") from e

        return self.serializer.serialize(user)

    async def update(self, user_id: UUID, body: UserUpdateSchema) -> UserSchema:
        """
        Обновляет информацию о пользователе
        """
        async with self.uow:
            user = await self.uow.user.update(user_id, body)

            if user is None:
                raise BaseException(f"Пользователь с ID {user_id} не найден")

        return self.serializer.serialize(user)

    async def delete(self, user_id: UUID, auth_user_id: UUID) -> None:
        """
        Удаляет пользователя из базы данных
        """
        if user_id == auth_user_id:
            raise BaseException("Нельзя удалить самого себя")

        user = await self.uow.user.get_user_by_id(user_id)

        if user and user.photo:
            # Удаление фотографии пользователя
            try:
                filename = os.path.basename(user.photo)
                filepath = os.path.join(settings.media.photo_path, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                logger.warning(f"Не удалось удалить фото пользователя {user_id}: {e}")

        async with self.uow:
            await self.uow.user.delete(user_id)

    async def update_password(self, user_id: UUID, body: UpdatePasswordUserSchema) -> None:
        """
        Обновляет пароль пользователя
        """
        async with self.uow:
            await self.uow.user.update_password(user_id, body)

    async def upload_photo(self, user_id: UUID, file: UploadFile) -> str:
        """
        Загружает фотографию пользователя
        """
        if not file.content_type.startswith("image/"):
            raise HTTPException(400, detail="Файл должен быть изображением")

        ext = file.filename.split('.')[-1].lower()

        async with self.uow:
            user = await self.uow.user.get_user_by_id(user_id)
            if not user:
                raise HTTPException(404, detail="Пользователь не найден")
            username = user.username

            filename = f"{username}.{ext}"
            photo_dir = settings.media.photo_path

            os.makedirs(settings.media.photo_path, exist_ok=True)

            for f in os.listdir(photo_dir):
                if f.startswith(f"{username}.") and f != filename:
                    try:
                        os.remove(os.path.join(photo_dir, f))
                    except Exception:
                        pass

            filepath = os.path.join(settings.media.photo_path, filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            photo_url = f"{settings.media.photo_url}/{filename}"

            await self.uow.user.update_photo(user_id, photo_url)

            return photo_url

    async def delete_photo(self, user_id: UUID) -> None:
        """
        Очищает фотографию пользователя
        """
        async with self.uow:
            user = await self.uow.user.get_user_by_id(user_id)
            if not user:
                raise HTTPException(404, detail="Пользователь не найден")

            if user.photo:
                try:
                    filename = os.path.basename(user.photo)
                    filepath = os.path.join(settings.media.photo_path, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception as e:
                    logger.warning(f"Не удалось удалить фото пользователя {user_id}: {e}")

            await self.uow.user.update_photo(user_id, None)
