import requests
from PyQt6.QtCore import pyqtSignal, QObject


class UpdateStatusWorker(QObject):
    """
    Воркер для асинхронного запроса статуса задачи с устройства.
    """
    progress = pyqtSignal(str)    # Для логов или прогресса (опционально)
    finished = pyqtSignal(dict)   # Передаёт ответ {"status": ..., ...}
    error = pyqtSignal(str)       # Сообщение об ошибке

    def __init__(self, device_api_url, task_id, parent=None):
        super().__init__(parent)
        self.device_api_url = device_api_url
        self.task_id = task_id

    def run(self):
        if self.task_id is None:
            self.error.emit("ID задачи не найден.")
            return

        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/status"
            self.progress.emit("Запрос статуса задачи...")
            resp = requests.get(url, timeout=3)
            if resp.status_code == 404:
                self.error.emit("Задача не найдена.")
                return
            resp.raise_for_status()
            data = resp.json()
            self.finished.emit(data)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                self.error.emit("Задача не найдена.")
            else:
                self.error.emit(f"HTTP ошибка: {e}")
        except Exception as e:
            self.error.emit(f"Ошибка при запросе статуса: {e}")
