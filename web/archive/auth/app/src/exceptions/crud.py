class CrudException(Exception):
    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


class CreateError(CrudException):
    def __init__(self, message: str = "Ошибка создания записи", *args: object) -> None:
        super().__init__(message, *args)


class NotFoundError(CrudException):
    def __init__(self, message: str = "Запись не найдена", *args: object) -> None:
        super().__init__(message, *args)


class UpdateError(CrudException):
    def __init__(self, message: str = "Ошибка редактирования записи", *args: object) -> None:
        super().__init__(message, *args)


class DeleteError(CrudException):
    def __init__(self, message: str = "Ошибка удаления записи", *args: object) -> None:
        super().__init__(message, *args)