from PyQt6.QtCore import QObject, pyqtSignal
import requests


class DeviceStatusWorker(QObject):
    """
    Класс для асинхронной проверки статуса устройства по IP
    """
    finished = pyqtSignal(str, str)   # ip, статус: 'online'/'offline'
    error = pyqtSignal(str, str)      # ip, текст ошибки

    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def run(self):
        """Асинхронно проверяет доступность устройства по IP."""
        try:
            resp = requests.head(f"http://{self.ip}:8080/", timeout=1)
            if resp.status_code < 500:
                self.finished.emit(self.ip, 'online')
            else:
                self.finished.emit(self.ip, 'offline')
        except Exception as e:
            self.finished.emit(self.ip, 'offline')
            self.error.emit(self.ip, str(e))
