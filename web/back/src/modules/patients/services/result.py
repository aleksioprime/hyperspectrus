from uuid import UUID

from sqlalchemy.exc import IntegrityError

from src.exceptions.base import BaseException
from src.models.patient import Result
from src.modules.patients.schemas.result import (
    ResultSchema, ResultCreateSchema, ResultUpdateSchema )
from src.modules.patients.repositories.uow import UnitOfWork


class ResultService:
    """ Сервис для управления результатами анализа """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_by_id(self, result_id: UUID) -> ResultSchema:
        """
        Выдаёт результат анализа по его ID
        """
        async with self.uow:
            result = await self.uow.result.get_by_id(result_id)

            if not result:
                raise BaseException(f"Результат анализа с ID {result_id} не найдена")

        return result

    async def create(self, body: ResultCreateSchema, user_id: UUID) -> ResultSchema:
        """
        Создаёт новый результат анализа
        """
        try:
            async with self.uow:
                result = Result(
                    session_id=body.session_id,
                    s_coefficient=body.s_coefficient,
                    mean_lesion_thb=body.mean_lesion_thb,
                    mean_skin_thb=body.mean_skin_thb,
                    notes=body.notes
                )
                await self.uow.result.create(result)

            return result

        except IntegrityError as e:
            if 'results_session_id_key' in str(e.orig):
                raise BaseException("У выбранного сеанса уже есть результат") from e
            raise BaseException("Ошибка создания результата") from e

    async def update(self, result_id: UUID, body: ResultUpdateSchema) -> ResultSchema:
        """
        Обновляет результат анализа по его ID
        """
        async with self.uow:
            result = await self.uow.result.update(result_id, body)

        return result

    async def delete(self, result_id: UUID) -> None:
        """
        Удаляет результат анализа по его ID
        """
        async with self.uow:
            await self.uow.result.delete(result_id)