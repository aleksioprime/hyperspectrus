import logging
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest

logger = logging.getLogger(__name__)

class DeviceStatusWorker(QObject):
    # Сигнал о завершении проверки: ip, статус ('online' или 'offline')
    finished = pyqtSignal(str, str)
    # Сигнал об ошибке: ip, строка ошибки
    error = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ip = None  # IP адрес текущего устройства для проверки
        self.manager = QNetworkAccessManager(self)  # Асинхронный менеджер сетевых запросов Qt
        self.reply = None  # Ссылка на текущий QNetworkReply (для отмены или очистки)

    def check(self, ip):
        """
        Запускает асинхронную HEAD-проверку статуса устройства по ip.
        Старый запрос (если был) будет отменён вызовом abort() из SessionDialog.
        """
        logger.debug(f"DeviceStatusWorker: start check {ip}")
        self.ip = ip
        url = QUrl(f"http://{self.ip}:8080/")
        request = QNetworkRequest(url)
        self.reply = self.manager.head(request)  # Асинхронный HEAD-запрос
        self.reply.finished.connect(self.on_finished)  # Обработка по завершению (успех или ошибка)

    def on_finished(self):
        """
        Слот: вызывается при завершении асинхронного HEAD-запроса.
        Гарантировано вызывается только один раз для каждого запроса (Qt гарантирует).
        """
        reply = self.reply  # Захватываем в переменную, чтобы избежать гонок
        self.reply = None   # Сразу очищаем ссылку, чтобы параллельные abort()/on_finished не конфликтовали

        if reply is None:
            logger.debug("DeviceStatusWorker: on_finished called, but no reply!")
            return

        # Получаем HTTP-код (для PyQt6 правильно так!)
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = reply.error()
        error_string = reply.errorString()
        logger.debug(f"DeviceStatusWorker: reply finished (ip={self.ip}, code={code}, error={error}, error_str={error_string})")

        if error == reply.NetworkError.NoError:
            # Нет ошибки, считаем online если HTTP-код < 500
            self.finished.emit(self.ip, 'online' if code is not None and code < 500 else 'offline')
        else:
            # Была ошибка, считаем offline
            self.finished.emit(self.ip, 'offline')
            self.error.emit(self.ip, error_string)

        reply.deleteLater()  # Корректная очистка объекта Qt

    def abort(self):
        """
        Отменяет текущий сетевой запрос, если он есть.
        Безопасен при повторных вызовах и параллельных с on_finished.
        """
        reply = self.reply
        self.reply = None  # Сразу очищаем ссылку (защита от гонок)

        if reply is not None:
            logger.debug(f"DeviceStatusWorker: aborting request to {self.ip}")
            reply.abort()       # Сообщаем Qt отменить запрос
            reply.deleteLater() # Корректная очистка объекта
        else:
            logger.debug(f"DeviceStatusWorker: abort() called but reply is already None")


class DeviceStatusRowWorker(DeviceStatusWorker):
    """
    Worker для отдельной строки таблицы (или можешь просто DeviceStatusWorker, если ip хранится в check()).
    """
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row