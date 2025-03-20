from pydantic import BaseModel, Field
from fastapi import Query


class BasePaginationParams(BaseModel):
    """ Базовый класс параметров пагинации """
    limit: int = Field(Query(alias='page_size', gt=0))
    offset: int = Field(Query(alias='page_number', ge=0))