import os
import requests
from sqlalchemy.orm import joinedload

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QPixmap

from db.db import SessionLocal
from db.models import Session, RawImage, DeviceBinding, ReconstructedImage
from ui.session.process_worker import ProcessWorker
from ui.session.download_worker import DownloadWorker


class SessionWidget(QWidget):
    """
    Окно просмотра и управления результатами сеанса.
    Показывает сведения о пациенте и сеансе, статус задачи, загрузку и просмотр фото (raw и processed).
    """

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Информация о сеансе")
        self.session = session
        self.device_api_url = f"http://{self.session.device_binding.ip_address}:8080"
        self.task_id = self.session.device_task_id

        # --- ВЕРХНИЙ БЛОК ---
        upper_layout = QHBoxLayout()

        # 1. Информация о пациенте/сеансе

        info_layout = QVBoxLayout()
        label_patient = QLabel(f"ФИО пациента: {self.session.patient.full_name}")
        label_patient.setWordWrap(True)
        info_layout.addWidget(label_patient)
        info_layout.addWidget(QLabel(f"Дата рождения: {self.session.patient.birth_date.strftime('%d.%m.%Y')}"))
        info_layout.addWidget(QLabel(f"Дата сеанса: {self.session.date.strftime('%d.%m.%Y %H:%M')}"))
        info_layout.addWidget(QLabel(f"Оператор: {self.session.operator.full_name if self.session.operator else ''}"))
        info_layout.addWidget(QLabel(f"Заметки: {self.session.notes or ''}"))

        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        upper_layout.addWidget(info_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # 2. Статус устройства, IP, кнопки
        device_layout = QVBoxLayout()
        label_device = QLabel(f"Устройство: {self.session.device_binding.device.name if self.session.device_binding else ''}")
        label_device.setWordWrap(True)
        device_layout.addWidget(label_device)
        ip_addr = self.session.device_binding.ip_address if self.session.device_binding else ""
        device_layout.addWidget(QLabel(f"IP: {ip_addr}"))
        self.status_label = QLabel("Статус: -")
        device_layout.addWidget(self.status_label)

        self.refresh_status_btn = QPushButton("Обновить статус")
        self.download_photos_btn = QPushButton("Загрузить фото с устройства")
        device_layout.addWidget(self.refresh_status_btn)
        device_layout.addWidget(self.download_photos_btn)

        device_widget = QWidget()
        device_widget.setLayout(device_layout)
        upper_layout.addWidget(device_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # 3. Общий анализ (заглушка, но будет динамически обновляться)
        analysis_layout = QVBoxLayout()
        self.analys_label = QLabel("Общий анализ: -")
        analysis_layout.addWidget(self.analys_label)
        self.s_coefficient = QLabel("S-коэффициент: -")
        analysis_layout.addWidget(self.s_coefficient)
        self.lesion_thb = QLabel("Thb (очаг): -")
        analysis_layout.addWidget(self.lesion_thb)
        self.skin_thb = QLabel("Thb (кожа): -")
        analysis_layout.addWidget(self.skin_thb)
        analysis_widget = QWidget()
        analysis_widget.setLayout(analysis_layout)
        upper_layout.addWidget(analysis_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # --- НИЖНИЙ БЛОК ---
        lower_layout = QHBoxLayout()

        # 1. Сырые фото: таблица и предпросмотр
        raw_side = QVBoxLayout()
        raw_side.addWidget(QLabel("Сырые снимки:"))

        raw_table_block = QHBoxLayout()
        self.raw_table = QTableWidget(0, 1)
        self.raw_table.setFixedWidth(100)
        self.raw_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.raw_table.setHorizontalHeaderLabels(["Спектр"])
        self.raw_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.raw_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.raw_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.raw_table.itemSelectionChanged.connect(self.on_raw_photo_selected)
        raw_table_block.addWidget(self.raw_table)

        self.raw_view = QLabel("Нет фото")
        self.raw_view.setMinimumSize(180, 135)
        self.raw_view.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.raw_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        raw_table_block.addWidget(self.raw_view)

        raw_side.addLayout(raw_table_block)
        lower_layout.addLayout(raw_side)

        # 2. Обработанные фото: таблица и предпросмотр (можно позже реализовать)
        proc_side = QVBoxLayout()
        proc_side.addWidget(QLabel("Обработанные снимки:"))

        proc_table_block = QHBoxLayout()
        self.proc_table = QTableWidget(0, 1)
        self.proc_table.setFixedWidth(100)
        self.proc_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.proc_table.setHorizontalHeaderLabels(["Хромофор"])
        self.proc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.proc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.proc_table.itemSelectionChanged.connect(self.on_proc_photo_selected)
        proc_table_block.addWidget(self.proc_table)

        self.proc_view = QLabel("Нет фото")
        self.proc_view.setMinimumSize(180, 135)
        self.proc_view.setAlignment(Qt.AlignmentFlag.AlignTop)
        proc_table_block.addWidget(self.proc_view)

        proc_side.addLayout(proc_table_block)
        lower_layout.addLayout(proc_side)

        bottom_button = QHBoxLayout()
        # --- Кнопка обработки ---
        self.process_btn = QPushButton("Обработка")
        self.process_btn.setFixedWidth(120)
        self.process_btn.setEnabled(False)
        bottom_button.addWidget(self.process_btn)

        self.processing_label = QLabel("Статус обработки: -")
        bottom_button.addWidget(self.processing_label)

        self.back_btn = QPushButton("Назад")
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.close)
        bottom_button.addStretch()
        bottom_button.addWidget(self.back_btn)

        # --- Основной layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(upper_layout)
        main_layout.addSpacing(3)
        main_layout.addLayout(lower_layout)
        main_layout.addLayout(bottom_button)

        # --- Сигналы ---
        self.refresh_status_btn.clicked.connect(self.update_task_status)
        self.download_photos_btn.clicked.connect(self.start_photo_download)
        self.process_btn.clicked.connect(self.process_results)

        # --- Инициализация данных ---
        self.thread = None
        self.download_worker = None
        self.processing_thread = None
        self.process_worker = None
        self.update_task_status()
        self.load_raw_photos()
        self.load_proc_photos()
        self.update_analysis_block()

    def refresh_session_data(self):
        session_db = SessionLocal()
        self.session = session_db.query(Session).options(
            joinedload(Session.patient),
            joinedload(Session.device_binding).joinedload(DeviceBinding.device),
            joinedload(Session.operator),
            joinedload(Session.result),
            ).get(self.session.id)
        session_db.close()
        self.update_analysis_block()

    def update_analysis_block(self):
        """
        Обновляет текст анализа по self.session.result.
        """
        result = self.session.result
        if result:
            self.analys_label.setText("Общий анализ: выполнен")
            self.s_coefficient.setText(f"S-коэффициент: {result.s_coefficient:.3f}")
            self.lesion_thb.setText(f"Thb (очаг): {result.mean_lesion_thb:.3f}")
            self.skin_thb.setText(f"Thb (кожа): {result.mean_skin_thb:.3f}")
        else:
            self.analys_label.setText("Общий анализ: не выполнен")

    def update_task_status(self):
        """
        Обновляет статус задачи на устройстве (по кнопке).
        Если задача не найдена — блокирует загрузку фото и обработку.
        """
        if self.task_id is None:
            self.status_label.setText("Статус: задача не найдена")
            self.download_photos_btn.setEnabled(False)
            return

        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/status"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 404:
                self.status_label.setText("Статус: задача не найдена")
                self.download_photos_btn.setEnabled(False)
                return
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "Статус: —")
            self.status_label.setText(status)
            # Включаем обработку только если фото уже есть локально и статус "completed"
            if status == "completed" and self.has_photos():
                self.process_btn.setEnabled(True)
            else:
                self.process_btn.setEnabled(False)
            self.download_photos_btn.setEnabled(True)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                self.status_label.setText("Статус: задача не найдена")
                self.download_photos_btn.setEnabled(False)
            else:
                self.status_label.setText("Статус: ошибка обновления")
                print(f"Ошибка при обновлении статуса: {e}")
                self.download_photos_btn.setEnabled(False)
        except Exception as e:
            self.status_label.setText("Статус: ошибка обновления")
            print(f"Ошибка при обновлении статуса: {e}")
            self.download_photos_btn.setEnabled(False)

    def load_raw_photos(self):
        """
        Загружает и отображает сырые фото (RawImage), связанные с этим сеансом.
        В таблице: №, спектр (wavelength).
        """
        session = SessionLocal()
        photos = (
            session.query(RawImage)
            .filter_by(session_id=self.session.id)
            .options(joinedload(RawImage.spectrum))
            .all()
        )
        session.close()
        self.raw_table.setRowCount(0)
        self._raw_paths = []  # сохраняем пути для предпросмотра
        for i, photo in enumerate(photos):
            self.raw_table.insertRow(i)
            spec_str = str(photo.spectrum.wavelength) if photo.spectrum and getattr(photo.spectrum, "wavelength", None) is not None else "?"
            self.raw_table.setItem(i, 0, QTableWidgetItem(spec_str))
            self._raw_paths.append(photo.file_path)
        # Заглушка в окне предпросмотра
        if self.raw_table.rowCount() == 0:
            self.raw_view.setText("Нет фото")
        else:
            self.raw_view.setText("Выберите фото слева")

        self.process_btn.setEnabled(self.has_photos())

    def load_proc_photos(self):
        """
        Загружает и отображает обработанные снимки (ReconstructedImage), связанные с этим сеансом.
        В таблице: №, хромофор (symbol).
        """
        session = SessionLocal()
        images = (
            session.query(ReconstructedImage)
            .filter_by(session_id=self.session.id)
            .options(joinedload(ReconstructedImage.chromophore))
            .all()
        )
        session.close()
        self.proc_table.setRowCount(0)
        self._proc_paths = []
        for i, img in enumerate(images):
            self.proc_table.insertRow(i)
            chrom_str = img.chromophore.symbol if img.chromophore else "?"
            self.proc_table.setItem(i, 0, QTableWidgetItem(chrom_str))
            self._proc_paths.append(img.file_path)
        if self.proc_table.rowCount() == 0:
            self.proc_view.setText("Нет фото")
        else:
            self.proc_view.setText("Выберите фото слева")


    def on_raw_photo_selected(self):
        """
        Показывает выбранное raw фото в предпросмотре.
        """
        selected = self.raw_table.selectedItems()
        if not selected:
            self.raw_view.setText("Выберите фото слева")
            return
        idx = selected[0].row()
        if idx < 0 or idx >= len(self._raw_paths):
            self.raw_view.setText("Файл не найден")
            return
        path = self._raw_paths[idx]
        if not os.path.isfile(path):
            self.raw_view.setText("Файл не найден")
            return
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.raw_view.setPixmap(pixmap.scaled(
                self.raw_view.width(), self.raw_view.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.raw_view.setText("Ошибка загрузки фото")

    def on_proc_photo_selected(self):
        """
        Показывает выбранное обработанное фото в предпросмотре.
        """
        selected = self.proc_table.selectedItems()
        if not selected:
            self.proc_view.setText("Выберите фото слева")
            return
        idx = selected[0].row()
        if idx < 0 or idx >= len(self._proc_paths):
            self.proc_view.setText("Файл не найден")
            return
        path = self._proc_paths[idx]
        if not os.path.isfile(path):
            self.proc_view.setText("Файл не найден")
            return
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.proc_view.setPixmap(pixmap.scaled(
                self.proc_view.width(), self.proc_view.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.proc_view.setText("Ошибка загрузки фото")


    def has_photos(self) -> bool:
        """
        Проверяет, есть ли в таблице загруженные фото.
        """
        return self.raw_table.rowCount() > 0

    def start_photo_download(self):
        if self.task_id is None:
            QMessageBox.warning(self, "Ошибка", "ID задачи не найден. Обновите статус.")
            return

        if self.thread is not None and self.thread.isRunning():
            QMessageBox.information(self, "Загрузка", "Загрузка уже выполняется.")
            return

        self.thread = QThread(self)
        self.download_worker = DownloadWorker(self.session.id, self.device_api_url)
        self.download_worker.task_id = self.task_id
        self.download_worker.moveToThread(self.thread)

        # Connect signals and slots
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)

        self.thread.started.connect(self.download_worker.run)
        # Clean up worker and thread
        self.download_worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        # Also ensure cleanup on error
        self.download_worker.error.connect(self.thread.quit) # Ensure thread quits on error
        # self.thread.finished.connect(self.download_worker.deleteLater) # Already connected via finished

        self.download_photos_btn.setEnabled(False)
        self.status_label.setText("Статус: Загрузка фото...")
        self.thread.start()

    def on_download_progress(self, message: str):
        self.status_label.setText(f"Статус: {message}")

    def on_download_finished(self, saved_count: int, message: str):
        QMessageBox.information(self, "Загрузка завершена", f"{message}\nСохранено фото: {saved_count}")
        self.load_raw_photos() # Refresh the list of raw photos
        self.process_btn.setEnabled(self.has_photos())
        self.download_photos_btn.setEnabled(True)
        self.status_label.setText(f"Статус: Загрузка завершена. {message}")
        # Reset thread and worker references
        self.thread = None
        self.download_worker = None


    def on_download_error(self, message: str):
        QMessageBox.warning(self, "Ошибка загрузки", message)
        self.download_photos_btn.setEnabled(True)
        self.status_label.setText(f"Статус: Ошибка загрузки. {message}")
        # Reset thread and worker references
        if self.thread and self.thread.isRunning(): # Ensure thread is quit if error signal is emitted before finished
            self.thread.quit()
            self.thread.wait() # Wait for thread to finish before deleting
        self.thread = None
        self.download_worker = None

    def on_processing_thread_finished(self):
        """Slot to clean up processing thread and worker."""
        if self.processing_thread: # Check if it hasn't been set to None already
            self.processing_thread.deleteLater()
        if self.process_worker: # Check if it hasn't been set to None already
            self.process_worker.deleteLater()
        self.processing_thread = None
        self.process_worker = None
        # Re-enable buttons after thread is confirmed finished
        self.process_btn.setEnabled(self.has_photos()) # Enable only if photos are present
        self.download_photos_btn.setEnabled(True)


    def process_results(self):
        """
        Initiates image processing in a separate thread using ProcessWorker.
        """
        if self.processing_thread is not None and self.processing_thread.isRunning():
            QMessageBox.information(self, "Обработка", "Процесс обработки уже запущен.")
            return

        if not self.has_photos():
            QMessageBox.warning(self, "Нет фото", "Сначала загрузите снимки с устройства!")
            return

        self.processing_thread = QThread(self)
        self.process_worker = ProcessWorker(session_id=self.session.id)
        self.process_worker.moveToThread(self.processing_thread)

        # Connect signals for progress, completion, and errors
        self.process_worker.progress.connect(self.on_processing_progress)
        self.process_worker.finished.connect(self.on_processing_finished)
        self.process_worker.error.connect(self.on_processing_error) # For unhandled exceptions in worker

        # Connect thread lifecycle signals
        self.processing_thread.started.connect(self.process_worker.run)
        # When worker signals it's done (finished or error), tell the thread to quit
        self.process_worker.finished.connect(self.processing_thread.quit)
        self.process_worker.error.connect(self.processing_thread.quit)

        # When the thread actually finishes, schedule cleanup
        self.processing_thread.finished.connect(self.on_processing_thread_finished)


        # Update UI: disable buttons, show status
        self.process_btn.setEnabled(False)
        self.download_photos_btn.setEnabled(False) # Disable photo downloads during processing
        self.processing_label.setText("Статус: Обработка изображений...")

        self.processing_thread.start()

    def on_processing_progress(self, message: str):
        """Handles progress updates from ProcessWorker."""
        self.processing_label.setText(f"Статус: Обработка... {message}")

    def on_processing_finished(self, success: bool, results_or_error: object):
        """Handles the finished signal from ProcessWorker."""
        if success:
            results_dict = results_or_error
            s_coefficient = results_dict.get("s_coefficient", 0.0)
            mean_lesion_thb = results_dict.get("mean_lesion_thb", 0.0)
            mean_skin_thb = results_dict.get("mean_skin_thb", 0.0)

            # Update UI labels for analysis results
            self.analys_label.setText("Общий анализ: выполнен (поточная)") # Indicate it's from threaded processing
            self.s_coefficient.setText(f"S-коэффициент: {s_coefficient:.3f}")
            self.lesion_thb.setText(f"Thb (очаг): {mean_lesion_thb:.3f}")
            self.skin_thb.setText(f"Thb (кожа): {mean_skin_thb:.3f}")

            self.load_proc_photos() # Refresh the table of processed images
            self.refresh_session_data() # Refresh session data which might update other UI parts

            QMessageBox.information(
                self,
                "Обработка завершена",
                f"Готово!\nS-коэффициент: {s_coefficient:.2f}\nTHb (очаг): {mean_lesion_thb:.2f}\nTHb (кожа): {mean_skin_thb:.2f}"
            )
            self.status_label.setText("Статус: Обработка успешно завершена.")
        else:
            error_message = str(results_or_error)
            QMessageBox.warning(self, "Ошибка обработки", error_message)
            self.processing_label.setText(f"Статус: Ошибка обработки. {error_message}")

        # Buttons are re-enabled in on_processing_thread_finished to ensure thread is fully done.
        # However, process_btn logic might need adjustment based on state (e.g. if it can be retried)
        # For now, it's handled by on_processing_thread_finished.

    def on_processing_error(self, message: str):
        """Handles unexpected errors from ProcessWorker."""
        QMessageBox.critical(self, "Критическая ошибка обработки", f"Произошла непредвиденная ошибка: {message}")
        self.processing_label.setText(f"Статус: Критическая ошибка обработки! {message}")
        # Buttons re-enabled by on_processing_thread_finished after thread quits.

    def closeEvent(self, event):
        # Ensure download thread is cleaned up if widget is closed
        if self.thread is not None and self.thread.isRunning():
            self.status_label.setText("Статус: Завершение загрузки фото...")
            self.thread.quit()
            self.thread.wait(3000) # Wait up to 3 seconds

        # Ensure processing thread is cleaned up if widget is closed
        if self.processing_thread is not None and self.processing_thread.isRunning():
            self.processing_label.setText("Статус: Завершение обработки...")
            self.processing_thread.quit()
            self.processing_thread.wait(5000) # Wait up to 5 seconds

        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # Центрируем окно
        screen = self.screen().availableGeometry()
        size = self.frameGeometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)