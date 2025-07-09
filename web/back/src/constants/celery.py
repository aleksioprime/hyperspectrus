from enum import Enum


class CeleryStatus(Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


CELERY_STATUS_MAP = {
    CeleryStatus.PENDING: "Ожидание",
    CeleryStatus.STARTED: "Выполняется",
    CeleryStatus.SUCCESS: "Завершено",
    CeleryStatus.FAILURE: "Ошибка",
    CeleryStatus.RETRY: "Повтор",
}