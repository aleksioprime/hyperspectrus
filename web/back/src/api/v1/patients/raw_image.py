"""
Модуль с эндпоинтами для управления изображениями
"""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.patients.dependencies.raw_image import get_raw_image_service
from src.modules.patients.dependencies.session import get_session_service
from src.modules.patients.schemas.raw_image import RawImageSchema, RawImageIdsSchema
from src.modules.patients.services.raw_image import RawImageService
from src.modules.patients.services.session import SessionService

from src.tasks.session import process_session


router = APIRouter()


@router.post(
    path='/upload/',
    summary='Загрузить исходные изображения',
    status_code=status.HTTP_201_CREATED,
    response_model=list[RawImageSchema],
)
async def upload_raw_image(
        service: Annotated[RawImageService, Depends(get_raw_image_service)],
        service_session: Annotated[SessionService, Depends(get_session_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={ RoleName.EMPLOYEE }))],
        session_id: UUID = Form(...),
        spectrum_ids: List[UUID] = Form(...),
        files: List[UploadFile] = File(...),
) -> list[RawImageSchema]:
    """
    Загружает новые исходные изображения
    """
    raw_images = await service.upload_files(session_id, spectrum_ids, files)

    if session_id:
        celery_task = process_session.delay(str(session_id))
        await service_session.set_processing_task_id(session_id, celery_task.id)

    return raw_images

@router.delete(
    path='/{raw_image_id}/',
    summary='Удалить исходное изображение',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_raw_image(
        raw_image_id: UUID,
        service: Annotated[RawImageService, Depends(get_raw_image_service)],
        service_session: Annotated[SessionService, Depends(get_session_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет исходное изображения по его ID
    """
    session_id = await service.delete(raw_image_id)

    if session_id:
        celery_task = process_session.delay(str(session_id))
        await service_session.set_processing_task_id(session_id, celery_task.id)

@router.post(
    path='/delete/',
    summary='Удалить изображения по списку ID',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_raw_images(
        data: RawImageIdsSchema,
        service: Annotated[RawImageService, Depends(get_raw_image_service)],
        service_session: Annotated[SessionService, Depends(get_session_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет исходное изображения по списку ID
    """
    session_ids = await service.bulk_delete(data.ids)

    for session_id in set(session_ids or []):
        if session_id:
            celery_task = process_session.delay(str(session_id))
            await service_session.set_processing_task_id(session_id, celery_task.id)