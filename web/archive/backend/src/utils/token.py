import time
from jwt import ExpiredSignatureError, InvalidTokenError, decode

from src.core.config import settings
from src.schemas.auth import UserJWT

class JWTHelper:
    """
    Класс для работы с JWT токенами
    """

    @staticmethod
    def decode(token: str) -> dict | None:
        """
        Проверяет подлинность и срок действия переданного JWT токена
        """

        try:
            decoded_token = decode(
                token,
                settings.jwt.secret_key,
                algorithms=[settings.jwt.algorithm],
            )

            if decoded_token["exp"] < time.time():
                return None

            user_data = {
                "user_id": decoded_token.get("sub"),
                "roles": decoded_token.get("roles", []),
                "token": token,
            }

            return UserJWT(**user_data)
        except (ExpiredSignatureError, InvalidTokenError):
            return None