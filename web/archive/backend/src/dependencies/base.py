from fastapi import Query

from src.schemas.base import BasePaginationParams


def get_pagination_params(
        page_size: int = Query(12, description='Количество записей на страницу'),
        page_number: int = Query(1, description='Номер текущей страницы'),
) -> BasePaginationParams:
    """ Получает параметры пагинации """

    limit = page_size if page_size > 0 else 12
    offset = (page_number - 1) * limit if page_number > 1 else 0

    return BasePaginationParams(
        limit=limit,
        offset=offset,
    )
