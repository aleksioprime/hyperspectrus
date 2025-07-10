import http
from typing import Optional, Set, Union

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.constants.role import RoleName
from src.utils.token import JWTHelper


class JWTBearer(HTTPBearer):
    def __init__(self, allowed_roles: Optional[Set[Union[RoleName, str]]] = None, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.allowed_roles = {role.value if isinstance(role, RoleName) else role for role in (allowed_roles or set())}

    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=http.HTTPStatus.FORBIDDEN,
                detail="Invalid authorization code.",
            )
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )
        decoded_token = self.parse_token(credentials.credentials)
        if not decoded_token:
            raise HTTPException(
                status_code=http.HTTPStatus.FORBIDDEN,
                detail="Invalid or expired token.",
            )

        if getattr(decoded_token, "is_superuser", False):
            return decoded_token

        roles = set(decoded_token.roles)
        if self.allowed_roles and not roles & self.allowed_roles:
            raise HTTPException(
                status_code=http.HTTPStatus.FORBIDDEN,
                detail="Недостаточно прав для доступа."
            )

        return decoded_token

    @staticmethod
    def parse_token(jwt_token: str) -> Optional[dict]:
        payload = JWTHelper().decode(jwt_token)
        return payload