import os
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QPushButton,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from db.db import SessionLocal
from db.models import Session, Patient, Device, DeviceBinding, User, RawImage, Spectrum

class SessionWidget(QWidget):
    """
    Окно просмотра и управления результатами сеанса.
    Показывает основные сведения, статус задачи устройства, позволяет загружать и просматривать фото.
    """

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Информация о сеансе")
        self.session = session
        self.device_api_url = f"http://{self.session.device_binding.ip_address}:8080"

        # Основная разметка
        main_layout = QVBoxLayout(self)

        # Форма с основной информацией о сеансе
        info_form = QFormLayout()
        info_form.addRow("ФИО пациента:", QLabel(self.session.patient.full_name))
        info_form.addRow("Дата рождения:", QLabel(self.session.patient.birth_date.strftime("%d.%m.%Y")))
        info_form.addRow("Дата сеанса:", QLabel(self.session.date.strftime("%d.%m.%Y %H:%M")))
        info_form.addRow("Оператор:", QLabel(self.session.operator.username if self.session.operator else ""))
        info_form.addRow("Устройство:", QLabel(self.session.device_binding.device.name if self.session.device_binding else ""))
        info_form.addRow("Заметки:", QLabel(self.session.notes or ""))
        main_layout.addLayout(info_form)

        # Блок статуса задачи и действия
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Статус задачи: —")
        self.refresh_status_btn = QPushButton("Обновить статус")
        self.download_photos_btn = QPushButton("Загрузить фото с устройства")
        self.process_btn = QPushButton("Обработка")
        self.process_btn.setEnabled(False)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.refresh_status_btn)
        status_layout.addWidget(self.download_photos_btn)
        status_layout.addWidget(self.process_btn)
        main_layout.addLayout(status_layout)

        # Горизонтальный сплиттер для таблицы и просмотра фото
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Таблица с локальными фотографиями (3 столбца: №, путь, спектр)
        self.photos_table = QTableWidget(0, 3)
        self.photos_table.setHorizontalHeaderLabels(["№", "Путь", "Спектр"])
        self.photos_table.setColumnWidth(0, 40)  # маленький столбец номера
        self.photos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.photos_table.setColumnWidth(2, 90)
        self.photos_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.photos_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.photos_table.itemSelectionChanged.connect(self.on_photo_selected)

        table_layout = QVBoxLayout()
        table_layout.addWidget(QLabel("Снимки:"))
        table_layout.addWidget(self.photos_table)
        table_widget = QWidget()
        table_widget.setLayout(table_layout)
        splitter.addWidget(table_widget)

        # Виджет для предпросмотра фото
        self.photo_viewer = QLabel("Нет фото")
        self.photo_viewer.setMinimumSize(320, 240)
        self.photo_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splitter.addWidget(self.photo_viewer)

        main_layout.addWidget(splitter)

        # Сигналы
        self.refresh_status_btn.clicked.connect(self.update_task_status)
        self.download_photos_btn.clicked.connect(self.download_photos)
        self.process_btn.clicked.connect(self.process_results)

        # Вспомогательные поля
        self.task_id = self.session.device_task_id

        # Инициализация: загрузка статуса и списка фото
        self.update_task_status()
        self.load_photos()

    def update_task_status(self):
        """
        Обновляет статус задачи на устройстве (по кнопке).
        Если задача не найдена — блокирует загрузку фото и обработку.
        """
        if self.task_id is None:
            self.status_label.setText("Статус задачи: задача не найдена")
            self.process_btn.setEnabled(False)
            self.download_photos_btn.setEnabled(False)
            return

        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/status"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 404:
                self.status_label.setText("Статус задачи: задача не найдена")
                self.download_photos_btn.setEnabled(False)
                self.process_btn.setEnabled(False)
                return
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "—")
            self.status_label.setText(f"Статус задачи: {status}")
            # Включаем обработку только если фото уже есть локально и статус "completed"
            if status == "completed" and self.has_photos():
                self.process_btn.setEnabled(True)
            else:
                self.process_btn.setEnabled(False)
            self.download_photos_btn.setEnabled(True)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                self.status_label.setText("Статус задачи: задача не найдена")
                self.download_photos_btn.setEnabled(False)
                self.process_btn.setEnabled(False)
            else:
                self.status_label.setText("Ошибка при обновлении статуса")
                print(f"Ошибка при обновлении статуса: {e}")
                self.process_btn.setEnabled(False)
                self.download_photos_btn.setEnabled(False)
        except Exception as e:
            self.status_label.setText("Ошибка при обновлении статуса")
            print(f"Ошибка при обновлении статуса: {e}")
            self.process_btn.setEnabled(False)
            self.download_photos_btn.setEnabled(False)

    def load_photos(self):
        """
        Загружает из базы и отображает только локально сохранённые фото (RawImage), связанные с этим сеансом.
        В таблице: №, путь, спектр (wavelength).
        """
        session = SessionLocal()
        # Подгружаем спектр сразу через joinedload для оптимизации
        from sqlalchemy.orm import joinedload
        photos = (
            session.query(RawImage)
            .filter_by(session_id=self.session.id)
            .options(joinedload(RawImage.spectrum))
            .all()
        )
        session.close()

        self.photos_table.setRowCount(0)
        for i, photo in enumerate(photos):
            self.photos_table.insertRow(i)
            self.photos_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.photos_table.setItem(i, 1, QTableWidgetItem(photo.file_path))
            # Показываем длину волны спектра (или "?" если данных нет)
            if photo.spectrum and getattr(photo.spectrum, "wavelength", None) is not None:
                spec_str = str(photo.spectrum.wavelength)
            else:
                spec_str = "?"
            self.photos_table.setItem(i, 2, QTableWidgetItem(spec_str))

        # Заглушка в окне предпросмотра
        if self.photos_table.rowCount() == 0:
            self.photo_viewer.setText("Нет фото")
        else:
            self.photo_viewer.setText("Выберите фото слева")

    def on_photo_selected(self):
        """
        Показывает выбранное фото в правом блоке.
        Если файл не найден — пишет "Файл не найден".
        """
        selected = self.photos_table.selectedItems()
        if not selected:
            self.photo_viewer.setText("Выберите фото слева")
            return
        path = self.photos_table.item(selected[0].row(), 1).text()
        if not os.path.isfile(path):
            self.photo_viewer.setText("Файл не найден")
            return
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.photo_viewer.setPixmap(pixmap.scaled(
                self.photo_viewer.width(), self.photo_viewer.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.photo_viewer.setText("Ошибка загрузки фото")

    def has_photos(self) -> bool:
        """
        Проверяет, есть ли в таблице загруженные фото.
        """
        return self.photos_table.rowCount() > 0

    def download_photos(self):
        """
        Скачивает фото через API устройства, сохраняет их в отдельную папку для каждой сессии,
        добавляет записи в таблицу RawImage с указанием spectrum_id.
        """
        if self.task_id is None:
            QMessageBox.warning(self, "Ошибка", "ID задачи не найден")
            return
        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/photos"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            photos = resp.json()
            print(photos)
            saved_count = 0

            # Корневая папка проекта (вверх на один уровень от текущего файла)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            photos_root = os.path.join(base_dir, "downloaded_photos")
            session_dir = os.path.join(photos_root, f"session_{self.session.id}")
            os.makedirs(session_dir, exist_ok=True)

            session_db = SessionLocal()
            for photo in photos:
                spectrum_id = photo.get("spectrum_id")
                # Проверяем, не существует ли уже такой снимок в базе
                exists = session_db.query(RawImage).filter_by(session_id=self.session.id, spectrum_id=spectrum_id).first()
                if exists:
                    continue

                # Скачиваем фото
                download_url = f"{self.device_api_url}/{photo.get('download_url')}"  # Желательно, чтобы прямая ссылка была в API
                if not download_url:
                    continue

                img_resp = requests.get(download_url, timeout=20)
                if img_resp.status_code == 200:
                    fname = os.path.join(session_dir, f"spectrum_{spectrum_id}.jpg")
                    with open(fname, "wb") as f:
                        f.write(img_resp.content)
                    # Добавляем запись в RawImage
                    raw_image = RawImage(
                        session_id=self.session.id,
                        file_path=fname,
                        spectrum_id=spectrum_id
                    )
                    session_db.add(raw_image)
                    saved_count += 1
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось скачать фото с spectrum_id={spectrum_id}")
            # Обновляем флаг загрузки фото в сеансе
            db_session = session_db.query(Session).get(self.session.id)
            db_session.photos_downloaded = True
            session_db.commit()
            session_db.close()
            QMessageBox.information(self, "Готово", f"Загружено фото: {saved_count}")
            self.load_photos()
            self.process_btn.setEnabled(self.has_photos())
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки фото: {e}")

    def process_results(self):
        """
        Запуск обработки фото (заглушка, расширьте под свои задачи).
        """
        QMessageBox.information(self, "Обработка", "Обработка запущена (пока заглушка)")

    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen().availableGeometry()
        size = self.frameGeometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        """
        Действия при закрытии окна (если потребуется).
        """
        event.accept()
