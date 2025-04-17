from typing import Annotated
from fastapi import Depends

from src.modules.patients.dependencies.uow import get_unit_of_work
from src.modules.patients.repositories.uow import UnitOfWork
from src.modules.patients.services.raw_image import RawImageService


def get_raw_image_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> RawImageService:
    """
    Возвращает экземпляр RawImageService с переданным UnitOfWork (UoW)
    """
    return RawImageService(uow=uow)