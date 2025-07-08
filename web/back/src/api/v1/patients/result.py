"""
Модуль с эндпоинтами для управления результатами анализа
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.patients.dependencies.result import get_result_service
from src.modules.patients.schemas.result import ResultSchema, ResultCreateSchema, ResultUpdateSchema
from src.modules.patients.services.result import ResultService


router = APIRouter()


@router.get(
    path='/{result_id}',
    summary='Получить детальную информацию о результате анализа',
    response_model=ResultSchema,
    status_code=status.HTTP_200_OK,
)
async def get_result(
        result_id: UUID,
        service: Annotated[ResultService, Depends(get_result_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> ResultSchema:
    """
    Получает детальную информацию о результате анализа
    """
    result = await service.get_by_id(result_id)
    return result


@router.post(
    path='/',
    summary='Создать результат анализа',
    status_code=status.HTTP_201_CREATED,
)
async def create_result(
        body: ResultCreateSchema,
        service: Annotated[ResultService, Depends(get_result_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> ResultSchema:
    """
    Создаёт новый результат анализа
    """
    result = await service.create(body, user.user_id)
    return result


@router.patch(
    path='/{result_id}',
    summary='Обновить результат анализа',
    response_model=ResultSchema,
    status_code=status.HTTP_200_OK,
)
async def update_result(
        result_id: UUID,
        body: ResultUpdateSchema,
        service: Annotated[ResultService, Depends(get_result_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> ResultSchema:
    """
    Обновляет результат анализа по его ID
    """
    result = await service.update(result_id, body)
    return result


@router.delete(
    path='/{result_id}',
    summary='Удалить результат анализа',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_result(
        result_id: UUID,
        service: Annotated[ResultService, Depends(get_result_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет результат анализа по его ID
    """
    await service.delete(result_id)