"""
Модуль с эндпоинтами для управления сеансами пациентов
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.patients.dependencies.session import get_session_service, get_session_params
from src.modules.patients.schemas.session import SessionSchema, SessionCreateSchema, SessionUpdateSchema, SessionDetailSchema, SessionQueryParams
from src.modules.patients.services.session import SessionService


router = APIRouter()


@router.get(
    path='/{session_id}',
    summary='Получить детальную информацию о сеансе',
    response_model=SessionDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_session(
        patient_id: UUID,
        session_id: UUID,
        service: Annotated[SessionService, Depends(get_session_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> SessionDetailSchema:
    """
    Получает детальную информацию о сеансе
    """
    session = await service.get_detail_by_id(patient_id, session_id)
    return session


@router.post(
    path='/',
    summary='Создать сеанс',
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
        patient_id: UUID,
        body: SessionCreateSchema,
        service: Annotated[SessionService, Depends(get_session_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> SessionSchema:
    """
    Создаёт новый сеанс
    """
    session = await service.create(body, user.user_id, patient_id)
    return session


@router.patch(
    path='/{session_id}',
    summary='Обновить сеанс',
    response_model=SessionSchema,
    status_code=status.HTTP_200_OK,
)
async def update_session(
        patient_id: UUID,
        session_id: UUID,
        body: SessionUpdateSchema,
        service: Annotated[SessionService, Depends(get_session_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> SessionSchema:
    """
    Обновляет сеанс по его ID
    """
    session = await service.update(body, patient_id, session_id)
    return session


@router.delete(
    path='/{session_id}',
    summary='Удалить сеанс',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(
        patient_id: UUID,
        session_id: UUID,
        service: Annotated[SessionService, Depends(get_session_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.USER}))],
) -> None:
    """
    Удаляет сеанс по его ID
    """
    await service.delete(patient_id, session_id)