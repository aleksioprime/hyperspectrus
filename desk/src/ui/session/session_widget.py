import os
import requests
from datetime import datetime
from sqlalchemy.orm import joinedload

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QSizePolicy,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QPixmap

from core.config import BASE_DIR
from db.db import get_db_session
from db.models import Session, RawImage, DeviceBinding, ReconstructedImage
from ui.session.process_worker import ProcessWorker
from ui.session.download_worker import DownloadWorker
from ui.session.update_worker import UpdateStatusWorker


class SessionWidget(QWidget):
    """
    Окно просмотра и управления результатами сеанса.
    Отображает информацию о пациенте, устройстве, статусе задачи, а также
    позволяет просматривать, загружать и обрабатывать фотографии
    """

    def __init__(self, session: Session, parent=None):
        """
        Инициализация виджета с основным интерфейсом для просмотра и управления сеансом
        """
        super().__init__(parent)
        self.setWindowTitle("Информация о сеансе")
        self.setFixedSize(900, 740)
        self.session = session
        self.device_api_url = f"http://{self.session.device_binding.ip_address}:8080"
        self.task_id = self.session.device_task_id

        # --- ВЕРХНИЙ БЛОК (информация о пациенте, устройстве, статус задачи, сырые фото) ---
        upper_layout = QHBoxLayout()

        # --- Информация о пациенте/сеансе/устройстве ---
        info_layout = QVBoxLayout()
        label_patient = QLabel(f"ФИО пациента: {self.session.patient.full_name}")
        info_layout.addWidget(label_patient)
        info_layout.addWidget(QLabel(f"Дата рождения: {self.session.patient.birth_date.strftime('%d.%m.%Y')}"))
        info_layout.addWidget(QLabel(f"Дата сеанса: {self.session.date.strftime('%d.%m.%Y %H:%M')}"))
        info_layout.addWidget(QLabel(f"Оператор: {self.session.operator.full_name if self.session.operator else ''}"))
        info_layout.addWidget(QLabel(f"Заметки: {self.session.notes or ''}"))
        label_device = QLabel(f"Устройство: {self.session.device_binding.device.name if self.session.device_binding else ''}")
        info_layout.addWidget(label_device)
        ip_addr = self.session.device_binding.ip_address if self.session.device_binding else ""
        info_layout.addWidget(QLabel(f"IP: {ip_addr}"))
        self.task_label = QLabel("Статус: не обновлён")
        info_layout.addWidget(self.task_label)

        # --- Кнопки управления устройством ---
        button_status_widget = QHBoxLayout()
        self.refresh_status_btn = QPushButton("Обновить статус")
        self.download_photos_btn = QPushButton("Загрузить фото с устройства")
        self.download_photos_btn.setEnabled(False)
        button_status_widget.addWidget(self.refresh_status_btn)
        button_status_widget.addWidget(self.download_photos_btn)
        info_layout.addLayout(button_status_widget)

        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        upper_layout.addWidget(info_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # --- Сырые фото: таблица и предпросмотр ---
        raw_photo = QVBoxLayout()
        raw_photo.addWidget(QLabel("Сырые снимки:"))

        raw_table_block = QHBoxLayout()
        self.raw_table = QTableWidget(0, 1)
        self.raw_table.setFixedSize(100, 240)
        self.raw_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.raw_table.setHorizontalHeaderLabels(["Спектр"])
        self.raw_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.raw_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.raw_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.raw_table.itemSelectionChanged.connect(self.on_raw_photo_selected)
        raw_table_block.addWidget(self.raw_table)

        self.raw_view = QLabel("Нет фото")
        self.raw_view.setFixedSize(320, 240)
        self.raw_view.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.raw_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        raw_table_block.addWidget(self.raw_view)
        raw_photo.addLayout(raw_table_block)

        raw_photo_widget = QWidget()
        raw_photo_widget.setLayout(raw_photo)
        upper_layout.addWidget(raw_photo_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # --- НИЖНИЙ БЛОК (обработанные фото, анализ, результаты) ---
        lower_layout = QHBoxLayout()

        # --- Обработанные фото: таблица и предпросмотр ---
        proc_photo = QVBoxLayout()
        proc_photo.addWidget(QLabel("Обработанные снимки:"))

        proc_table_block = QHBoxLayout()
        self.proc_table = QTableWidget(0, 1)
        self.proc_table.setFixedSize(100, 240)
        self.proc_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.proc_table.setHorizontalHeaderLabels(["Хромофор"])
        self.proc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.proc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.proc_table.itemSelectionChanged.connect(self.on_proc_photo_selected)
        proc_table_block.addWidget(self.proc_table)

        self.proc_view = QLabel("Нет фото")
        self.proc_view.setFixedSize(320, 240)
        self.proc_view.setAlignment(Qt.AlignmentFlag.AlignTop)
        proc_table_block.addWidget(self.proc_view)
        proc_photo.addLayout(proc_table_block)

        proc_photo_widget = QWidget()
        proc_photo_widget.setLayout(proc_photo)
        lower_layout.addWidget(proc_photo_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # --- Аналитический блок и результаты ---
        analysis_layout = QVBoxLayout()
        self.analys_label = QLabel("Общий анализ: -")
        analysis_layout.addWidget(self.analys_label)
        self.s_coefficient = QLabel("S-коэффициент: -")
        analysis_layout.addWidget(self.s_coefficient)
        self.lesion_thb = QLabel("Thb (очаг): -")
        analysis_layout.addWidget(self.lesion_thb)
        self.skin_thb = QLabel("Thb (кожа): -")
        analysis_layout.addWidget(self.skin_thb)

        bottom_img_layout = QHBoxLayout()

        # --- Изображение результата: контур ---
        contour_path_layout = QVBoxLayout()
        contour_path_layout.addWidget(QLabel("Контур очага (Otsu):"))
        self.contour_path_img = QLabel("Изображение")
        self.contour_path_img.setFixedSize(192, 144)
        contour_path_layout.addWidget(self.contour_path_img)

        # --- Изображение результата: THb ---
        thb_path_layout = QVBoxLayout()
        thb_path_layout.addWidget(QLabel("Карта THb:"))
        self.thb_path_img = QLabel("Изображение")
        self.thb_path_img.setFixedSize(192, 144)
        thb_path_layout.addWidget(self.thb_path_img)

        bottom_img_layout.addLayout(contour_path_layout)
        bottom_img_layout.addLayout(thb_path_layout)
        analysis_layout.addLayout(bottom_img_layout)
        analysis_widget = QWidget()
        analysis_widget.setLayout(analysis_layout)

        lower_layout.addWidget(analysis_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # --- Кнопки управления внизу окна ---
        bottom_button = QHBoxLayout()
        self.process_btn = QPushButton("Обработка")
        self.process_btn.setFixedWidth(120)
        self.process_btn.setEnabled(False)
        bottom_button.addWidget(self.process_btn)

        self.back_btn = QPushButton("Назад")
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.close)
        bottom_button.addStretch()
        bottom_button.addWidget(self.back_btn)

        # --- Лог событий внизу окна ---
        bottom_status = QVBoxLayout()
        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setFixedHeight(80)
        self.log_widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        bottom_status.addWidget(self.log_widget)
        bottom_status.addWidget(self.progress_bar)

        # --- Основной layout окна ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(upper_layout)
        main_layout.addSpacing(1)
        main_layout.addLayout(lower_layout)
        main_layout.addLayout(bottom_button)
        main_layout.addLayout(bottom_status)

        # --- Сигналы ---
        self.refresh_status_btn.clicked.connect(self.update_task_status)
        self.download_photos_btn.clicked.connect(self.start_photo_download)
        self.process_btn.clicked.connect(self.process_results)

        # --- Инициализация потоков и загрузка данных ---
        self.thread = None
        self.download_worker = None
        self.processing_thread = None
        self.process_worker = None
        # self.update_task_status()
        self.load_raw_photos()
        self.load_proc_photos()
        self.update_analysis_block()

    def refresh_session_data(self):
        """
        Перезагружает объект сеанса из базы данных (например, после обработки).
        """
        with get_db_session() as session_db:
            self.session = session_db.query(Session).options(
                joinedload(Session.patient),
                joinedload(Session.device_binding).joinedload(DeviceBinding.device),
                joinedload(Session.operator),
                joinedload(Session.result),
                ).get(self.session.id)
        self.update_analysis_block()

    def log_message(self, message: str):
        """
        Записывает сообщение в лог событий с временной меткой
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.appendPlainText(f"[{timestamp}] {message}")
        self.log_widget.verticalScrollBar().setValue(self.log_widget.verticalScrollBar().maximum())

    def update_analysis_block(self):
        """
        Обновляет блок анализа
        """
        result = self.session.result

        pixmap_contour_path = QPixmap(os.path.join(BASE_DIR, "assets/images/no_image.png"))
        pixmap_thb_path = QPixmap(os.path.join(BASE_DIR, "assets/images/no_image.png"))

        if result:
            self.analys_label.setText("Общий анализ: выполнен")
            self.s_coefficient.setText(f"S-коэффициент: {result.s_coefficient:.3f}")
            self.lesion_thb.setText(f"Thb (очаг): {result.mean_lesion_thb:.3f}")
            self.skin_thb.setText(f"Thb (кожа): {result.mean_skin_thb:.3f}")

            # Загрузка изображения контура (если путь существует)
            if result.contour_path and os.path.isfile(result.contour_path):
                pixmap_contour_path = QPixmap(result.contour_path)

            # Загрузка изображения THb (если путь существует)
            if result.thb_path and os.path.isfile(result.thb_path):
                pixmap_thb_path = QPixmap(result.thb_path)

        else:
            self.analys_label.setText("Общий анализ: не выполнен")
            self.s_coefficient.setText("S-коэффициент: -")
            self.lesion_thb.setText("Thb (очаг): -")
            self.skin_thb.setText("Thb (кожа): -")

        if not pixmap_contour_path.isNull():
            self.contour_path_img.setPixmap(pixmap_contour_path.scaled(
                self.contour_path_img.width(), self.contour_path_img.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.contour_path_img.setText("Нет данных")

        if not pixmap_thb_path.isNull():
            self.thb_path_img.setPixmap(pixmap_thb_path.scaled(
                self.thb_path_img.width(), self.thb_path_img.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.thb_path_img.setText("Нет данных")

    def update_task_status(self):
        """
        Обновляет статус задачи на устройстве через отдельный поток
        """
        if self.task_id is None:
            self.task_label.setText("Статус: задача не найдена")
            self.download_photos_btn.setEnabled(False)
            return

        if hasattr(self, "_status_thread") and self._status_thread is not None and self._status_thread.isRunning():
            self.log_message("Обновление статуса уже выполняется...")
            return

        self._status_thread = QThread(self)
        self._status_worker = UpdateStatusWorker(self.device_api_url, self.task_id)
        self._status_worker.moveToThread(self._status_thread)

        self._status_worker.progress.connect(self.log_message)
        self._status_worker.finished.connect(self.on_status_finished)
        self._status_worker.error.connect(self.on_status_error)
        self._status_thread.started.connect(self._status_worker.run)
        self._status_worker.finished.connect(self._status_thread.quit)
        self._status_worker.error.connect(self._status_thread.quit)
        self._status_thread.finished.connect(self._status_thread.deleteLater)
        self._status_worker.finished.connect(self._status_worker.deleteLater)
        self._status_worker.error.connect(self._status_worker.deleteLater)

        self.progress_bar.setVisible(True)
        self._status_thread.start()

    def on_status_finished(self, data: dict):
        """
        Слот вызывается после успешного завершения асинхронного запроса статуса задачи
        """
        status = data.get("status", "Статус: —")
        self.task_label.setText(status)

        self.download_photos_btn.setEnabled(status == "completed")
        self.process_btn.setEnabled(self.has_photos())

        self._status_thread = None
        self.progress_bar.setVisible(False)

    def on_status_error(self, message: str):
        """
        Слот вызывается при ошибке обновления статуса задачи
        """
        self.task_label.setText(f"Статус: ошибка")
        self.download_photos_btn.setEnabled(False)
        self.log_message(f"Ошибка статуса: {message}")
        self._status_thread = None
        self.progress_bar.setVisible(False)

    def load_raw_photos(self):
        """
        Загружает и отображает сырые фото, связанные с текущим сеансом.
        В таблице отображается спектр (длина волны)
        """
        with get_db_session() as session:
            photos = (
                session.query(RawImage)
                .filter_by(session_id=self.session.id)
                .options(joinedload(RawImage.spectrum))
                .all()
            )
        self.raw_table.setRowCount(0)
        self._raw_paths = []
        for i, photo in enumerate(photos):
            self.raw_table.insertRow(i)
            spec_str = str(photo.spectrum.wavelength) if photo.spectrum and getattr(photo.spectrum, "wavelength", None) is not None else "?"
            self.raw_table.setItem(i, 0, QTableWidgetItem(spec_str))
            self._raw_paths.append(photo.file_path)

        # Показываем заглушку, если фото не выбрано
        pixmap_raw_view = QPixmap(os.path.join(BASE_DIR, "assets/images/no_image.png"))
        if not pixmap_raw_view.isNull():
            self.raw_view.setPixmap(pixmap_raw_view.scaled(
                self.raw_view.width(), self.raw_view.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.raw_view.setText("Нет данных")

        self.process_btn.setEnabled(self.has_photos())

    def load_proc_photos(self):
        """
        Загружает и отображает обработанные снимки, связанные с этим сеансом.
        В таблице — хромофор (symbol).
        """
        with get_db_session() as session:
            images = (
                session.query(ReconstructedImage)
                .filter_by(session_id=self.session.id)
                .options(joinedload(ReconstructedImage.chromophore))
                .all()
            )
        self.proc_table.setRowCount(0)
        self._proc_paths = []
        for i, img in enumerate(images):
            self.proc_table.insertRow(i)
            chrom_str = img.chromophore.symbol if img.chromophore else "?"
            self.proc_table.setItem(i, 0, QTableWidgetItem(chrom_str))
            self._proc_paths.append(img.file_path)

        # Показываем заглушку, если фото не выбрано
        pixmap_proc_view = QPixmap(os.path.join(BASE_DIR, "assets/images/no_image.png"))
        if not pixmap_proc_view.isNull():
            self.proc_view.setPixmap(pixmap_proc_view.scaled(
                self.proc_view.width(), self.proc_view.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.proc_view.setText("Нет данных")

    def on_raw_photo_selected(self):
        """
        Показывает выбранное raw-фото в окне предпросмотра.
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
        Показывает выбранное обработанное фото в окне предпросмотра
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
        Проверяет, есть ли в таблице загруженные фото
        """
        return self.raw_table.rowCount() > 0

    def start_photo_download(self):
        """
        Начинает загрузку снимков с устройства в отдельном потоке
        """
        if self.task_id is None:
            QMessageBox.warning(self, "Ошибка", "ID задачи не найден. Обновите статус")
            return

        if self.thread is not None and self.thread.isRunning():
            QMessageBox.information(self, "Загрузка", "Загрузка уже выполняется")
            return

        self.thread = QThread(self)
        self.download_worker = DownloadWorker(self.session.id, self.device_api_url)
        self.download_worker.task_id = self.task_id
        self.download_worker.moveToThread(self.thread)

        # Подключение сигналов и слотов
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)

        self.thread.started.connect(self.download_worker.run)
        self.download_worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_worker.error.connect(self.thread.quit)

        self.download_photos_btn.setEnabled(False)
        self.log_message("Загрузка фото...")
        self.progress_bar.setVisible(True)
        self.thread.start()

    def on_download_progress(self, message: str):
        """
        Обновляет лог прогресса при загрузке фото
        """
        self.log_message(f"{message}")

    def on_download_finished(self, saved_count: int, message: str):
        """
        Вызывается при завершении загрузки фото
        """
        QMessageBox.information(self, "Загрузка завершена", f"{message}\nСохранено фото: {saved_count}")
        self.load_raw_photos()
        self.process_btn.setEnabled(self.has_photos())
        self.download_photos_btn.setEnabled(True)
        self.log_message(f"Загрузка завершена. {message}")
        # Сброс потоков
        self.thread = None
        self.download_worker = None
        self.progress_bar.setVisible(False)

    def on_download_error(self, message: str):
        """
        Обработка ошибок при загрузке фото.
        """
        QMessageBox.warning(self, "Ошибка загрузки", message)
        self.download_photos_btn.setEnabled(True)
        self.log_message(f"Ошибка загрузки. {message}")
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.download_worker = None
        self.progress_bar.setVisible(False)

    def on_processing_thread_finished(self):
        """
        Слот для корректного завершения и очистки потока обработки.
        """
        if self.processing_thread:
            self.processing_thread.deleteLater()
        if self.process_worker:
            self.process_worker.deleteLater()
        self.processing_thread = None
        self.process_worker = None
        self.process_btn.setEnabled(self.has_photos())

    def process_results(self):
        """
        Запускает обработку изображений в отдельном потоке
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

        self.process_worker.progress.connect(self.on_processing_progress)
        self.process_worker.finished.connect(self.on_processing_finished)
        self.process_worker.error.connect(self.on_processing_error)
        self.processing_thread.started.connect(self.process_worker.run)
        self.process_worker.finished.connect(self.processing_thread.quit)
        self.process_worker.error.connect(self.processing_thread.quit)
        self.processing_thread.finished.connect(self.on_processing_thread_finished)

        self.process_btn.setEnabled(False)
        self.download_photos_btn.setEnabled(False)
        self.log_message("Обработка изображений...")

        self.progress_bar.setVisible(True)
        self.processing_thread.start()

    def on_processing_progress(self, message: str):
        """
        Обновляет лог событий при выполнении обработки.
        """
        self.log_message(f"Обработка... {message}")

    def on_processing_finished(self, success: bool, results_or_error: object):
        """
        Вызывается после завершения обработки изображений.
        В случае успеха обновляет интерфейс, иначе — показывает ошибку
        """
        if success:
            results_dict = results_or_error
            s_coefficient = results_dict.get("s_coefficient", 0.0)
            mean_lesion_thb = results_dict.get("mean_lesion_thb", 0.0)
            mean_skin_thb = results_dict.get("mean_skin_thb", 0.0)

            self.analys_label.setText("Общий анализ: выполнен (поточная)")
            self.s_coefficient.setText(f"S-коэффициент: {s_coefficient:.3f}")
            self.lesion_thb.setText(f"Thb (очаг): {mean_lesion_thb:.3f}")
            self.skin_thb.setText(f"Thb (кожа): {mean_skin_thb:.3f}")

            self.load_proc_photos()
            self.refresh_session_data()

            QMessageBox.information(
                self,
                "Обработка завершена",
                f"Готово!\nS-коэффициент: {s_coefficient:.2f}\nTHb (очаг): {mean_lesion_thb:.2f}\nTHb (кожа): {mean_skin_thb:.2f}"
            )
            self.log_message("Обработка успешно завершена.")
        else:
            error_message = str(results_or_error)
            QMessageBox.warning(self, "Ошибка обработки", error_message)
            self.log_message(f"Ошибка обработки. {error_message}")

        self.progress_bar.setVisible(False)

    def on_processing_error(self, message: str):
        """
        Обработка критических ошибок при выполнении обработки изображений.
        """
        QMessageBox.critical(self, "Критическая ошибка обработки", f"Произошла непредвиденная ошибка: {message}")
        self.log_message(f"Критическая ошибка обработки! {message}")
        self.progress_bar.setVisible(False)

    def closeEvent(self, event):
        """
        Обеспечивает корректное завершение потоков при закрытии окна.
        """
        if self.thread is not None and self.thread.isRunning():
            self.log_message("Завершение загрузки фото...")
            self.thread.quit()
            self.thread.wait(3000)

        if self.processing_thread is not None and self.processing_thread.isRunning():
            self.log_message("Завершение обработки...")
            self.processing_thread.quit()
            self.processing_thread.wait(5000)

        super().closeEvent(event)

    def showEvent(self, event):
        """
        Центрирует окно при отображении.
        """
        super().showEvent(event)
        screen = self.screen().availableGeometry()
        size = self.frameGeometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
