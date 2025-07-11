from typing import Annotated
from fastapi import Depends, Query

from src.modules.patients.dependencies.uow import get_unit_of_work
from src.modules.patients.repositories.uow import UnitOfWork
from src.modules.patients.services.session import SessionService



def get_session_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> SessionService:
    """
    Возвращает экземпляр SessionService с переданным UnitOfWork (UoW)
    """
    return SessionService(uow=uow)