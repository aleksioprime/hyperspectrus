import datetime


def get_current_utc_time() -> datetime.datetime:
    """
    Возвращает текущее UTC время
    """

    return datetime.datetime.now(datetime.UTC)