"""
Модуль с эндпоинтами для управления изображениями
"""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from starlette import status

from src.core.schemas import UserJWT
from src.constants.role import RoleName
from src.core.security import JWTBearer
from src.modules.patients.dependencies.raw_image import get_raw_image_service
from src.modules.patients.schemas.raw_image import RawImageSchema, RawImageUpdateSchema, RawImageIdsSchema
from src.modules.patients.services.raw_image import RawImageService


router = APIRouter()


@router.post(
    path='/upload',
    summary='Загрузить исходные изображения',
    status_code=status.HTTP_201_CREATED,
    response_model=list[RawImageSchema],
)
async def upload_raw_image(
        service: Annotated[RawImageService, Depends(get_raw_image_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={ RoleName.EMPLOYEE }))],
        session_id: UUID = Form(...),
        spectrum_ids: List[UUID] = Form(...),
        files: List[UploadFile] = File(...),
) -> list[RawImageSchema]:
    """
    Загружает новые исходные изображения
    """
    raw_images = await service.upload_files(session_id, spectrum_ids, files)
    return raw_images


@router.post("/upload-debug")
async def debug_upload_raw_image(request: Request):
    form = await request.form()

    print("\n\n=== [DEBUG] RAW FORM DATA ===")
    for key in form:
        print(f"{key}: {form.getlist(key) if hasattr(form, 'getlist') else form[key]}")
    print("=== [END DEBUG] ===\n\n")

    return {"detail": "ok"}


@router.patch(
    path='/{raw_image_id}',
    summary='Обновить информацию об исходном изображении',
    response_model=RawImageSchema,
    status_code=status.HTTP_200_OK,
)
async def update_raw_image(
        raw_image_id: UUID,
        body: RawImageUpdateSchema,
        service: Annotated[RawImageService, Depends(get_raw_image_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> RawImageSchema:
    """
    Обновляет информацию об исходном изображении по его ID
    """
    raw_image = await service.update(raw_image_id, body)
    return raw_image


@router.delete(
    path='/{raw_image_id}',
    summary='Удалить исходное изображение',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_raw_image(
        raw_image_id: UUID,
        service: Annotated[RawImageService, Depends(get_raw_image_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет исходное изображения по его ID
    """
    await service.delete(raw_image_id)


@router.post(
    path='/delete',
    summary='Удалить изображения по списку ID',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_raw_images(
        data: RawImageIdsSchema,
        service: Annotated[RawImageService, Depends(get_raw_image_service)],
        user: Annotated[UserJWT, Depends(JWTBearer(allowed_roles={RoleName.EMPLOYEE}))],
) -> None:
    """
    Удаляет исходное изображения по списку ID
    """
    await service.bulk_delete(data.ids)