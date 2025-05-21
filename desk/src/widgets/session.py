import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QPushButton,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer

from db.db import SessionLocal
from db.models import Session, Patient, Device, User

class SessionWidget(QWidget):
    """
    Окно просмотра и управления результатами сеанса.
    Показывает основные сведения, статус задачи устройства, позволяет загружать фото и запускать обработку.
    """

    def __init__(self, session: Session, device_api_url: str = None, parent=None):
        """
        :param session: объект Session (sqlalchemy)
        :param device_api_url: http://IP:8080 (адрес устройства)
        """
        super().__init__(parent)
        self.setWindowTitle("Информация о сеансе")
        self.session = session
        self.device_api_url = device_api_url or self.detect_device_api_url()

        # UI
        main_layout = QVBoxLayout(self)
        info_form = QFormLayout()
        # Базовая информация о сеансе
        info_form.addRow("ФИО пациента:", QLabel(self.session.patient.full_name))
        info_form.addRow("Дата рождения:", QLabel(self.session.patient.birth_date.strftime("%d.%m.%Y")))
        info_form.addRow("Дата сеанса:", QLabel(self.session.date.strftime("%d.%m.%Y %H:%M")))
        info_form.addRow("Оператор:", QLabel(self.session.operator.username if self.session.operator else ""))
        info_form.addRow("Устройство:", QLabel(self.session.device.name if self.session.device else ""))
        info_form.addRow("Заметки:", QLabel(self.session.notes or ""))

        main_layout.addLayout(info_form)

        # Статус задачи на устройстве
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Статус задачи: —")
        self.refresh_status_btn = QPushButton("Обновить статус")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.refresh_status_btn)
        main_layout.addLayout(status_layout)

        # Таблица фото
        self.photos_table = QTableWidget(0, 2)
        self.photos_table.setHorizontalHeaderLabels(["№", "Путь"])
        self.photos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.photos_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.photos_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(QLabel("Снимки:"))
        main_layout.addWidget(self.photos_table)

        # Кнопки действий
        actions_layout = QHBoxLayout()
        self.download_photos_btn = QPushButton("Загрузить фото")
        self.process_btn = QPushButton("Обработка")  # Пока заглушка
        self.process_btn.setEnabled(False)  # Активируется, когда фото загружены и статус completed
        actions_layout.addWidget(self.download_photos_btn)
        actions_layout.addWidget(self.process_btn)
        main_layout.addLayout(actions_layout)

        # Сигналы
        self.refresh_status_btn.clicked.connect(self.update_task_status)
        self.download_photos_btn.clicked.connect(self.download_photos)
        self.process_btn.clicked.connect(self.process_results)

        # Автообновление статуса
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(5000)  # 5 секунд
        self.status_timer.timeout.connect(self.update_task_status)
        self.status_timer.start()

        # Инициализация — загрузка статуса и фото
        self.task_id = self.session.device_task_id
        self.update_task_status(initial=True)

    def detect_device_api_url(self) -> str:
        """
        Определяет URL API устройства по ip, хранящемуся в привязке.
        (Для примера — можно сделать по self.session.device или device_binding)
        """
        # Здесь должен быть способ получить ip устройства из DeviceBinding или другого источника
        # Например: self.session.device.device_binding[0].ip_address
        # Здесь стоит заглушка — подставьте свою логику!
        return "http://127.0.0.1:8080"

    def update_task_status(self, initial=False):
        """
        Обновляет статус задачи на устройстве.
        """
        if self.task_id is None:
            self.status_label.setText("Статус задачи: задача не найдена")
            self.process_btn.setEnabled(False)
            return

        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/status"
            resp = requests.get(url, timeout=3)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "—")
            self.status_label.setText(f"Статус задачи: {status}")
            if status == "completed":
                self.download_photos_btn.setEnabled(True)
                if self.has_photos():
                    self.process_btn.setEnabled(True)
            else:
                self.download_photos_btn.setEnabled(True)
                self.process_btn.setEnabled(False)
            if not initial:
                self.load_photos()
        except Exception as e:
            self.status_label.setText(f"Ошибка при обновлении статуса: {e}")
            self.download_photos_btn.setEnabled(False)
            self.process_btn.setEnabled(False)

    def load_photos(self):
        """
        Загружает и отображает список фотографий для задачи.
        """
        if self.task_id is None:
            self.photos_table.setRowCount(0)
            return
        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/photos"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            photos = resp.json()
            self.photos_table.setRowCount(0)
            for i, photo in enumerate(photos):
                self.photos_table.insertRow(i)
                self.photos_table.setItem(i, 0, QTableWidgetItem(str(photo.get("index"))))
                self.photos_table.setItem(i, 1, QTableWidgetItem(photo.get("path", "")))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить фото:\n{e}")
            self.photos_table.setRowCount(0)

    def has_photos(self) -> bool:
        """
        Проверяет, есть ли в таблице загруженные фото.
        """
        return self.photos_table.rowCount() > 0

    def download_photos(self):
        """
        Скачивает фото через API устройства и сохраняет их локально.
        """
        if self.task_id is None:
            QMessageBox.warning(self, "Ошибка", "ID задачи не найден")
            return
        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/photos"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            photos = resp.json()
            # Здесь пример: скачиваем все фото по очереди
            for photo in photos:
                index = photo.get("index")
                download_url = f"{self.device_api_url}/tasks/{self.task_id}/photos/{index}/download"
                img_resp = requests.get(download_url, timeout=20)
                if img_resp.status_code == 200:
                    # Сохраняем файл в папку 'downloaded_photos' (создать если нет)
                    import os
                    os.makedirs("downloaded_photos", exist_ok=True)
                    fname = f"downloaded_photos/session_{self.session.id}_photo_{index}.jpg"
                    with open(fname, "wb") as f:
                        f.write(img_resp.content)
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось скачать фото №{index}")
            QMessageBox.information(self, "Готово", f"Фотографии успешно загружены в папку downloaded_photos")
            self.load_photos()
            self.process_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки фото: {e}")

    def process_results(self):
        """
        Запуск обработки фото (заглушка, расширьте под свои задачи!).
        """
        QMessageBox.information(self, "Обработка", "Обработка запущена (пока заглушка)")

    def closeEvent(self, event):
        """
        Останавливает таймер обновления при закрытии окна.
        """
        self.status_timer.stop()
        event.accept()
