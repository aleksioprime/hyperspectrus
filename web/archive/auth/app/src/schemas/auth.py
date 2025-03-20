from pydantic import BaseModel, Field


class RegisterSchema(BaseModel):
    """
    Схема для регистрации пользователя.
    Определяет поля, необходимые для создания нового пользователя
    """

    login: str = Field(..., description="Логин пользователя")
    password: str = Field(..., description="Пароль пользователя")
    first_name: str = Field(..., description="Имя пользователя")
    last_name: str = Field(..., description="Фамилия пользователя")
    email: str = Field(..., description="Email пользователя")


class AuthSchema(BaseModel):
    """
    Схема для аутентификации пользователя.
    Определяет поля, необходимые для входа в систему
    """

    login: str = Field(..., description="Логин пользователя")
    password: str = Field(..., description="Пароль пользователя")