from uuid import UUID
from typing import List

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.models.user import User
from src.modules.users.repositories.uow import UnitOfWork
from src.modules.users.schemas.user import UserCreateSchema, UserUpdateSchema, UserSchema, UserQueryParams
from src.modules.users.serializers.user import BaseSerializer
from src.exceptions.base import BaseException


class UserService:

    def __init__(self, uow: UnitOfWork, serializer: BaseSerializer):
        self.uow = uow
        self.serializer = serializer

    async def get_user_all(self, params: UserQueryParams) -> List[UserSchema]:
        """
        Выдаёт информацию обо всех пользователях
        """
        async with self.uow:
            users = await self.uow.user.get_user_all(params)

        return [self.serializer.serialize(user) for user in users]

    async def get_user_by_id(self, user_id: UUID) -> UserSchema:
        """
        Выдаёт информацию о пользователе по его ID
        """
        async with self.uow:
            user = await self.uow.user.get_user_with_roles(user_id)
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
                )
                role = await self.uow.user.get_or_create_default_role()
                user.roles.append(role)

                await self.uow.user.create(user)
            except IntegrityError as e:
                raise BaseException("Пользователь уже существует") from e

        return self.serializer.serialize(user)

    async def update(self, user_id: UUID, body: UserUpdateSchema) -> UserSchema:
        """
        Обновляет информацию о пользователе
        """
        async with self.uow:
            user = await self.uow.user.update(user_id, body)
        return self.serializer.serialize(user)

    async def delete(self, user_id: UUID, auth_user_id: UUID) -> None:
        """
        Удаляет пользователя из базы данных
        """
        if user_id == auth_user_id:
            raise BaseException("Нельзя удалить самого себя")

        async with self.uow:
            await self.uow.user.delete(user_id)

    async def role_add(self, user_id: UUID, role_id: UUID):
        """
        Добавляет роль к пользователю
        """
        async with self.uow:
            user = await self.uow.user.get_user_by_id(user_id)
            if not user:
                raise BaseException("Пользователь не найден")

            role = await self.uow.user.get_role(role_id)
            if not role:
                raise BaseException("Роль не найдена")

            if await self.uow.user.has_role(user_id, role_id):
                raise BaseException("Роль уже назначена")

            await self.uow.user.add_role(user_id, role_id)

    async def role_remove(self, user_id: UUID, role_id: UUID):
        """
        Удаляет роль у пользователя
        """
        async with self.uow:
            user = await self.uow.user.get_user_by_id(user_id)
            if not user:
                raise BaseException("Пользователь не найден")

            role = await self.uow.user.get_role(role_id)
            if not role:
                raise BaseException("Роль не найдена")

            if not await self.uow.user.has_role(user_id, role_id):
                raise BaseException("Роль уже назначена")

            await self.uow.user.remove_role(user_id, role_id)
