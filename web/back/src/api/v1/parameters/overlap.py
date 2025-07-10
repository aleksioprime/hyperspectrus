"""
Модуль с эндпоинтами для управления спектрами светодиода
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.parameters.dependencies.overlap import get_overlap_coefficient_service
from src.modules.parameters.schemas.overlap import OverlapCoefficientSchema, OverlapCoefficientCreateSchema, OverlapCoefficientUpdateSchema
from src.modules.parameters.services.overlap import OverlapCoefficientService


router = APIRouter()


@router.post(
    path='/',
    summary='Создать коэффициент перекрытия',
    status_code=status.HTTP_201_CREATED,
)
async def create_overlap_coefficient(
        body: OverlapCoefficientCreateSchema,
        service: Annotated[OverlapCoefficientService, Depends(get_overlap_coefficient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> OverlapCoefficientSchema:
    """
    Создаёт новый коэффициент перекрытия
    """
    overlap_coefficient = await service.create(body)
    return overlap_coefficient


@router.patch(
    path='/{overlap_coefficient_id}/',
    summary='Обновить коэффициент перекрытия',
    response_model=OverlapCoefficientSchema,
    status_code=status.HTTP_200_OK,
)
async def update_overlap_coefficient(
        overlap_coefficient_id: UUID,
        body: OverlapCoefficientUpdateSchema,
        service: Annotated[OverlapCoefficientService, Depends(get_overlap_coefficient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> OverlapCoefficientSchema:
    """
    Обновляет коэффициент перекрытия по его ID
    """
    overlap_coefficient = await service.update(overlap_coefficient_id, body)
    return overlap_coefficient


@router.delete(
    path='/{overlap_coefficient_id}/',
    summary='Удалить коэффициент перекрытия',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_overlap_coefficient(
        overlap_coefficient_id: UUID,
        service: Annotated[OverlapCoefficientService, Depends(get_overlap_coefficient_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет коэффициент перекрытия по его ID
    """
    await service.delete(overlap_coefficient_id)