from fastapi import Query

from src.core.schemas import BasePaginationParams


def get_pagination_params(
        limit: int = Query(12, description='Количество записей на страницу'),
        offset: int = Query(1, description='Номер текущей страницы'),
) -> BasePaginationParams:
    """ Получает параметры пагинации """

    limit = limit if limit > 0 else 12
    offset = (offset - 1) * limit if offset > 1 else 0

    return BasePaginationParams(
        limit=limit,
        offset=offset,
    )