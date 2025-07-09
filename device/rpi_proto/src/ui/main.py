"""Главное окно управления задачами и съёмкой на Raspberry Pi."""
import os
import shutil
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QLabel, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QSizePolicy, QComboBox, QCheckBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, QTimer, QThread

from config.settings import icon_path
from services.photo import save_photo_for_task, clear_photos_for_task, get_photos_for_task
# Управление светодиодами напрямую через GPIO без Arduino
from services.leds import LedController
from services.hotspot import enable_hotspot, disable_hotspot
from services.shoot_worker import ShootWorker
from ui.camera import CameraWidget
from ui.gallery import GalleryWidget
from ui.confirm import ConfirmDialog
from models.db import SessionLocal, PhotoTask


logger = logging.getLogger(__name__)


class CameraApp(QWidget):
    """Главное окно: камера, задачи, точка доступа и съёмка с подсветкой.

    Подсветка управляется напрямую через GPIO без использования Arduino.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyperspectrus")

        self.shooting_in_progress = False
        self.tasks_map = {}
        self.hotspot_active = False
        self.hotspot_state = None

        # Авто-включение точки доступа при наличии сохранённого состояния
        state_file = os.path.expanduser("~/.hotspot_state.json")
        if os.path.exists(state_file):
            print("📶 Сохранённое состояние найдено. Включаем точку доступа...")
            success, state = enable_hotspot()
            if success:
                self.hotspot_active = True
                self.hotspot_state = state
                print("✅ Точка доступа восстановлена.")
            else:
                print("⚠️ Не удалось включить точку доступа автоматически.")

        # --- Верхняя панель: задача + переключатель точки доступа ---
        self.task_combo = QComboBox()
        self.task_combo.setFixedHeight(38)
        self.task_combo.setContentsMargins(0, 0, 0, 0)
        self.task_combo.currentIndexChanged.connect(self.update_buttons_state)

        self.clear_tasks_btn = QPushButton()
        self.clear_tasks_btn.setIcon(QIcon(icon_path("delete_task.png")))  # Подберите свой значок
        self.clear_tasks_btn.setIconSize(QSize(28, 28))
        self.clear_tasks_btn.setFixedSize(38, 38)
        self.clear_tasks_btn.setToolTip("Удалить все задачи")
        self.clear_tasks_btn.clicked.connect(self.clear_all_tasks)

        self.hotspot_toggle_btn = QPushButton()
        self.hotspot_toggle_btn.setCheckable(True)
        self.hotspot_toggle_btn.setIconSize(QSize(28, 28))
        self.hotspot_toggle_btn.setFixedSize(38, 38)
        self.hotspot_toggle_btn.clicked.connect(self.toggle_hotspot)

        self.ip_btn = QPushButton("IP")
        self.ip_btn.setFixedSize(40, 38)
        self.ip_btn.clicked.connect(self.show_ip_address)

        lbl = QLabel("Задача:")
        lbl.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.task_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.task_combo.setFixedHeight(38)

        self.confirm_mode_checkbox = QCheckBox("Снимки по кнопке")
        self.confirm_mode_checkbox.setChecked(False)
        self.confirm_mode_checkbox.setStyleSheet("margin-left: 12px;")

        top_panel = QHBoxLayout()
        top_panel.setContentsMargins(6, 0, 6, 6)
        top_panel.setSpacing(4)
        top_panel.addWidget(self.task_combo, stretch=1)
        top_panel.addWidget(self.clear_tasks_btn)
        top_panel.addWidget(self.hotspot_toggle_btn)
        top_panel.addWidget(self.ip_btn)

        top_panel.addWidget(self.confirm_mode_checkbox)

        # Обновление иконки и текста при старте
        if self.hotspot_active:
            self.hotspot_toggle_btn.setChecked(True)
            self.hotspot_toggle_btn.setIcon(QIcon(icon_path("wifi_on.png")))
        else:
            self.hotspot_toggle_btn.setChecked(False)
            self.hotspot_toggle_btn.setIcon(QIcon(icon_path("wifi_off.png")))

        # --- Камера + боковая панель ---
        # Виджет камеры использует picamera2 для работы через CSI-порт
        self.camera_widget = CameraWidget()

        # --- Основные действия ---
        self.photo_btn = QPushButton()
        self.photo_btn.setIcon(QIcon(icon_path("camera.png")))
        self.gallery_btn = QPushButton()
        self.gallery_btn.setIcon(QIcon(icon_path("gallery.png")))
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(icon_path("trash.png")))
        for btn in [self.photo_btn, self.gallery_btn, self.delete_btn]:
            btn.setIconSize(QSize(48, 48))
            btn.setFixedHeight(70)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet("padding: 0px; margin: 0px; border: none;")
        self.photo_btn.clicked.connect(self.photo_btn_handler)
        self.gallery_btn.clicked.connect(self.show_photos)
        self.delete_btn.clicked.connect(self.delete_photos)

        self._waiting_for_confirm = False

        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        for btn in [self.photo_btn, self.gallery_btn, self.delete_btn]:
            btn_layout.addWidget(btn)

        btn_panel = QWidget()
        btn_panel.setLayout(btn_layout)
        btn_panel.setFixedWidth(110)

        top_layout = QHBoxLayout()
        top_panel.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        top_layout.addWidget(self.camera_widget, stretch=1)
        top_layout.addWidget(btn_panel, stretch=0)

        # --- Строка состояния ---
        self.status_bar = QLabel()
        self.status_bar.setContentsMargins(0, 0, 0, 0)
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet("background-color: #222; color: white; padding-left: 8px;")
        if self.hotspot_active:
            self.status_bar.setText("Точка доступа включена")

        # --- Главный layout ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(top_panel)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.status_bar)
        self.setLayout(main_layout)

        # --- Автоматическое обновление задач ---
        self.task_update_timer = QTimer()
        self.task_update_timer.timeout.connect(self.update_tasks)
        self.task_update_timer.start(3000)

        self.update_tasks()

        # Контроллер светодиодов
        self.led_controller = LedController()
        self.led_controller.button.when_pressed = self.on_gpio_photo_button

    def show_ip_address(self):
        """Выводит IP-адрес wlan0 в статусную строку."""
        import socket
        import fcntl
        import struct

        def get_ip_address(ifname):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                return socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(),
                    0x8915,  # SIOCGIFADDR
                    struct.pack('256s', ifname[:15].encode('utf-8'))
                )[20:24])
            except Exception:
                return None

        ip = get_ip_address("wlan0")
        if ip:
            self.status_bar.setText(f"IP-адрес устройства: {ip}")
        else:
            self.status_bar.setText("IP-адрес не получен")

    def update_tasks(self):
        """
        Обновляет выпадающий список задач.
        Если задач нет — показывает "Нет задач" и блокирует действия.
        """
        db = SessionLocal()
        tasks = db.query(PhotoTask).order_by(PhotoTask.created_at.desc()).all()
        db.close()

        # --- Добавляем вручную тестовую задачу ---
        test_task = PhotoTask(
            id="test_task",
            title="Тестовая задача",
            status="test",
            spectra=[520, 660, 810, 850, 900, 940],
            created_at=datetime.utcnow()
        )
        tasks.insert(0, test_task)

        # Запомним текущий выбор и количество задач до обновления
        prev_task_id = self.task_combo.currentData()
        prev_count = self.task_combo.count()

        self.task_combo.blockSignals(True)
        self.task_combo.clear()
        self.tasks_map = {}

        if not tasks:
            self.task_combo.addItem("Нет задач", None)
            self.task_combo.setEnabled(False)
            self.photo_btn.setEnabled(False)
            self.gallery_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        else:
            for idx, task in enumerate(tasks):
                text = f"{task.title} [{task.status}]"
                self.task_combo.addItem(text, task.id)
                self.tasks_map[task.id] = task
            self.task_combo.setEnabled(True)

            # Если задач стало больше — выбрать последнюю (новую)
            # Если нет — попытаться восстановить предыдущий выбор
            if len(tasks) > prev_count:
                last_index = self.task_combo.count() - 1
                self.task_combo.setCurrentIndex(last_index)
            else:
                # Найти индекс старого task_id
                idx = self.task_combo.findData(prev_task_id)
                if idx != -1:
                    self.task_combo.setCurrentIndex(idx)
                else:
                    # Если старого нет — выбрать последнюю
                    self.task_combo.setCurrentIndex(self.task_combo.count() - 1)

        self.task_combo.blockSignals(False)
        self.clear_tasks_btn.setEnabled(len(tasks) > 1)

    def clear_all_tasks(self):
        """Удаляет все задачи и связанные фотографии."""
        reply = QMessageBox.question(
            self, "Очистить все задачи",
            "Вы уверены, что хотите удалить ВСЕ задачи и связанные фотографии?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        db = SessionLocal()
        tasks = db.query(PhotoTask).all()
        task_ids = [task.id for task in tasks]
        for task in tasks:
            db.delete(task)
        db.commit()
        db.close()

        # Теперь удаляем папки
        from config.settings import PHOTO_DIR  # или свой путь
        for task_id in task_ids:
            dir_path = os.path.join(PHOTO_DIR, f"task_{task_id}")
            if os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except Exception as e:
                    print(f"Ошибка удаления папки {dir_path}: {e}")

        self.status_bar.setText("Все задачи и фотографии удалены")
        self.update_tasks()
        self.update_buttons_state()


    def get_selected_task(self):
        """
        Возвращает объект выбранной задачи (или None, если задач нет или выбрано "Нет задач").
        """
        idx = self.task_combo.currentIndex()
        if idx < 0:
            return None
        task_id = self.task_combo.currentData()
        if not task_id or task_id not in self.tasks_map:
            return None
        return self.tasks_map[task_id]

    def take_photos(self):
        """Запускает серию фотографирования по выбранной задаче (в отдельном потоке)."""
        if self.shooting_in_progress:
            QMessageBox.warning(self, "Съёмка уже идёт", "Подождите завершения текущей съёмки.")
            return

        logger.info(f"Запуск новой съёмки")
        self.shooting_in_progress = True
        self.disable_all_buttons()
        self.status_bar.setText("Начинаю съёмку...")
        QApplication.processEvents()

        task = self.get_selected_task()
        if not task:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу!")
            self.shooting_in_progress = False
            self.update_buttons_state()
            return

        if getattr(task, "id", None) == "test_task":
            self.current_task_id = "test_task"
            test_mode = True
        else:
            self.current_task_id = task.id
            test_mode = False

        self.photo_index = 0
        clear_photos_for_task(task.id)
        self.current_spectra = task.spectra
        by_button = self.confirm_mode_checkbox.isChecked()

        # --- Создаём и запускаем воркер ---
        self.worker_thread = QThread()
        self.worker = ShootWorker(
            spectra=self.current_spectra,
            camera_widget=self.camera_widget,
            led_controller=self.led_controller,
            save_func=save_photo_for_task,
            task_id=self.current_task_id,
            test_mode=test_mode,
            by_button=by_button
        )
        self.worker.button_wait.connect(self.on_button_wait)
        self.worker.moveToThread(self.worker_thread)
        self.worker.progress.connect(self.status_bar.setText)
        self.worker.finished.connect(self.on_shooting_finished)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_gpio_photo_button(self):
        logger.info("Нажата кнопка GPIO")
        if not self.shooting_in_progress:
            QTimer.singleShot(0, self.take_photos)

    def photo_btn_handler(self):
        if self._waiting_for_confirm:
            self.on_photo_confirm()
        else:
            self.take_photos()

    def on_shooting_finished(self):
        """Завершение съёмки: обновляет интерфейс и статус задачи."""
        self._waiting_for_confirm = False
        self.photo_btn.setIcon(QIcon(icon_path("camera.png")))

        if self.current_task_id != "test_task":
            db = SessionLocal()
            task = db.query(PhotoTask).get(self.current_task_id)
            if task:
                task.status = "completed"
                db.commit()
            db.close()
            self.status_bar.setText("Съёмка завершена")
        else:
            self.status_bar.setText("Тестовая съёмка завершена")
        self.shooting_in_progress = False

        self.update_tasks()
        self.update_buttons_state()

        self.led_controller.button.when_pressed = self.on_gpio_photo_button

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None

    def on_button_wait(self, idx):
        # Отключить take_photos, если был
        self._waiting_for_confirm = True
        self.photo_btn.setEnabled(True)
        self.photo_btn.setIcon(QIcon(icon_path("camera_next.png")))
        self.led_controller.button.when_pressed = lambda: self.on_photo_confirm(gpio=True)

    def on_photo_confirm(self, checked=False, gpio=False):
        logger.info(f"Подтверждение кадра через {'GPIO' if gpio else 'GUI'}")
        self.photo_btn.setEnabled(False)
        self._waiting_for_confirm = False
        self.worker.button_pressed()
        self.led_controller.button.when_pressed = None

    def delete_photos(self):
        """Удаляет фотографии для выбранной задачи и сбрасывает её статус."""
        task = self.get_selected_task()
        if not task:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу!")
            return
        reply = QMessageBox.question(self, "Удалить", "Удалить все фотографии выбранной задачи?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            clear_photos_for_task(task.id)
            db = SessionLocal()
            db_task = db.query(PhotoTask).get(task.id)
            if db_task:
                db_task.status = "pending"
                db.commit()
            db.close()
            self.status_bar.setText("Фотографии удалены")
            self.update_tasks()
            self.update_buttons_state()

    def show_photos(self):
        """Открывает галерею для текущей задачи."""
        task = self.get_selected_task()
        if not task:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу!")
            return
        self.gallery = GalleryWidget(task.id)
        self.gallery.setWindowTitle("📁 Галерея")
        self.gallery.destroyed.connect(lambda: self.activateWindow())
        self.gallery.showFullScreen()

    def update_buttons_state(self):
        """Обновляет состояние кнопок в зависимости от наличия фото и процесса съёмки."""
        if self.shooting_in_progress:
            for btn in [self.photo_btn, self.gallery_btn, self.delete_btn, self.clear_tasks_btn]:
                btn.setEnabled(False)
            self.hotspot_toggle_btn.setEnabled(False)
            self.task_combo.setEnabled(False)
            return
        task = self.get_selected_task()
        has_photos = bool(task and get_photos_for_task(task.id))
        # Кнопки действий
        self.photo_btn.setEnabled(bool(task) and task.status != "completed")
        self.gallery_btn.setEnabled(has_photos)
        self.delete_btn.setEnabled(has_photos)
        self.hotspot_toggle_btn.setEnabled(True)
        self.task_combo.setEnabled(True)

    def disable_all_buttons(self):
        for btn in [self.photo_btn, self.gallery_btn, self.delete_btn, self.clear_tasks_btn]:
            btn.setEnabled(False)
        self.hotspot_toggle_btn.setEnabled(False)
        self.task_combo.setEnabled(False)

    def toggle_hotspot(self):
        """Переключает точку доступа (WiFi AP)."""
        if self.hotspot_toggle_btn.isChecked():
            if not ConfirmDialog.confirm(self, "Включить точку", "Вы точно хотите включить точку доступа?", "Да", "Нет"):
                self.hotspot_toggle_btn.setChecked(False)
                return
            # ВКЛЮЧЕНИЕ ТОЧКИ
            success, state = enable_hotspot()
            if success:
                self.hotspot_active = True
                self.hotspot_state = state  # сохраняем для восстановления
                self.hotspot_toggle_btn.setIcon(QIcon(icon_path("wifi_on.png")))
                self.status_bar.setText("Точка доступа включена")
            else:
                self.hotspot_toggle_btn.setChecked(False)
                self.status_bar.setText("Не удалось включить точку доступа")
        else:
            if not ConfirmDialog.confirm(self, "Выключить точку", "Вы точно хотите отключить точку доступа?", "Да", "Нет"):
                self.hotspot_toggle_btn.setChecked(True)
                return
            # ВЫКЛЮЧЕНИЕ ТОЧКИ
            if hasattr(self, "hotspot_state"):
                disabled = disable_hotspot(self.hotspot_state)
            else:
                disabled = disable_hotspot()  # fallback
            if disabled:
                self.hotspot_active = False
                self.hotspot_toggle_btn.setIcon(QIcon(icon_path("wifi_off.png")))
                self.status_bar.setText("Точка доступа выключена")
            else:
                self.hotspot_toggle_btn.setChecked(True)
                self.status_bar.setText("Не удалось выключить точку доступа")

    def showEvent(self, event):
        super().showEvent(event)
        self.update_tasks()

    def closeEvent(self, event):
        """Закрытие приложения и освобождение ресурсов."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.camera_widget.close()
        event.accept()

    def abort_shooting(self, reason: str):
        """Прерывает съёмку, очищает фото и выводит причину."""
        self.shooting_in_progress = False
        self.status_bar.setText(f"❌ Съёмка прервана: {reason}")
        clear_photos_for_task(self.current_task_id)
        self.update_buttons_state()
