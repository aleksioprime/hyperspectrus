from uuid import UUID
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

from src.models.patient import Result
from src.modules.patients.schemas.result import ResultSchema, ResultUpdateSchema


class ResultRepository:
    """
    Репозиторий для работы с результатами анализа
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, result_id: UUID) -> ResultSchema:
        """ Возвращает результат анализа по его ID """
        query = select(Result).where(Result.id == result_id)
        result = await self.session.execute(query)
        return result.scalars().unique().one_or_none()

    async def create(self, result: Result) -> ResultSchema:
        """ Создаёт новый результат анализа """
        self.session.add(result)

    async def update(self, result_id: UUID, body: ResultUpdateSchema) -> Optional[ResultSchema]:
        """ Обновляет результат анализа по его ID """
        update_data = {key: value for key, value in body.dict(exclude_unset=True).items()}
        if not update_data:
            raise NoResultFound(f"Нет данных для обновления")

        stmt = (
            update(Result)
            .filter_by(id=result_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        return await self.get_by_id(result_id)

    async def delete(self, result_id: UUID) -> bool:
        """ Удаляет результат анализа по его ID """
        result = await self.get_by_id(result_id)
        if not result:
            raise NoResultFound(f"Результат анализа с ID {result_id} не найден")

        await self.session.delete(result)
