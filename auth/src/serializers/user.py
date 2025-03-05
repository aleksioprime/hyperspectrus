from abc import ABC, abstractmethod
from typing import Any

from src.models.user import User
from src.schemas.user import UserSchema, RoleSchema


class BaseSerializer(ABC):
    """
    Базовый класс для сериализации объектов.
    """

    @abstractmethod
    def serialize(self, instance: Any) -> Any:
        """
        Преобразует объект модели в Pydantic-схему
        """
        pass


class UserSerializer(BaseSerializer):
    """
    Класс для преобразования данных пользователя в Pydantic-схемы
    """

    @staticmethod
    def serialize(user: User) -> UserSchema:
        """
        Преобразует объект пользователя в Pydantic-схему UserSchema
        """
        roles = [RoleSchema.from_orm(role) for role in user.roles]  # Преобразование ролей
        user_dict = user.__dict__.copy()  # Копирование данных пользователя
        user_dict['roles'] = roles  # Добавление списка ролей
        return UserSchema.parse_obj(user_dict)
