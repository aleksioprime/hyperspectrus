import time

from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, QTimer

from config.settings import icon_path, SPECTRA
from services.photo import save_photo, clear_photos, get_photos
from services.arduino import ArduinoController, ArduinoWatcher
from ui.camera import CameraWidget
from ui.gallery import GalleryWidget


class CameraApp(QWidget):
    def __init__(self):
        """
        Инициализирует главное окно камеры с:
        - виджетом камеры;
        - кнопками для съёмки, галереи, загрузки и удаления фото;
        - статусной строкой;
        - мониторингом подключения Arduino в фоновом потоке.
        """
        super().__init__()
        self.setCursor(Qt.BlankCursor)
        self.setWindowTitle("Hyperspectrus")
        self.setFixedSize(480, 320)

        # Виджет камеры
        self.camera_widget = CameraWidget()
        self.camera_widget.setFixedSize(380, 320)

        # Статусная строка
        self.status_bar = QLabel()
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet("background-color: #222; color: white; padding-left: 8px;")

        # Кнопки управления
        self.photo_btn = QPushButton()
        self.photo_btn.setIcon(QIcon(icon_path("camera.png")))

        self.gallery_btn = QPushButton()
        self.gallery_btn.setIcon(QIcon(icon_path("gallery.png")))

        self.upload_btn = QPushButton()
        self.upload_btn.setIcon(QIcon(icon_path("upload.png")))

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(icon_path("trash.png")))

        for btn in [self.photo_btn, self.gallery_btn, self.upload_btn, self.delete_btn]:
            btn.setIconSize(QSize(48, 48))
            btn.setFixedHeight(70)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet("padding: 0px; margin: 0px; border: none;")

        self.photo_btn.clicked.connect(self.take_photos)
        self.gallery_btn.clicked.connect(self.show_photos)
        self.upload_btn.clicked.connect(self.upload_photos)
        self.delete_btn.clicked.connect(self.delete_photos)

        # Вертикальный блок кнопок
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        for btn in [self.photo_btn, self.gallery_btn, self.upload_btn, self.delete_btn]:
            btn_layout.addWidget(btn)

        # Горизонтальный слой: камера + кнопки
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        top_layout.addWidget(self.camera_widget)
        top_layout.addLayout(btn_layout)

        # Общий layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.status_bar)
        self.setLayout(main_layout)

        # Мониторинг состояния Arduino
        self.arduino_available = False
        self.arduino_watcher = ArduinoWatcher()
        self.arduino_watcher.status_changed.connect(self.on_arduino_status_changed)
        self.arduino_watcher.start()

    def on_arduino_status_changed(self, available: bool, port: str):
        """
        Обновляет состояние флага подключения Arduino и интерфейса:
        - обновляет статусную строку;
        - включает/выключает кнопку съёмки.
        """
        self.arduino_available = available
        if available:
            self.status_bar.setText(f"Arduino подключена ({port})")
        else:
            self.status_bar.setText("Arduino не подключена")
        self.update_buttons_state()

    def take_photos(self):
        """
        Инициирует серию съёмок с управляемой подсветкой через Arduino.
        Каждый кадр делается в указанном спектре из SPECTRA. Управление подсветкой
        синхронизировано с Arduino через командный протокол (SET / PHOTO_DONE).
        """
        self.status_bar.setText("Начинаю съёмку...")
        self.disable_all_buttons()
        QApplication.processEvents()

        if not self.arduino_available:
            QMessageBox.warning(self, "Ошибка", "Arduino не подключён")
            return

        clear_photos()

        self.photo_index = 0
        self.arduino = ArduinoController()
        self.start_next_photo()

    def start_next_photo(self):
        """
        Отправляет следующую команду подсветки Arduino на основе текущего индекса в SPECTRA,
        и запускает отсроченный захват фото через QTimer. Заканчивает серию, если достигнут конец списка.
        """
        if self.photo_index >= len(SPECTRA):
            self.arduino.send_and_wait("PHOTO_DONE", "OFF_DONE")
            self.arduino.close()
            self.status_bar.setText("Съёмка завершена")
            self.update_buttons_state()
            return

        # Отправляем команду включения подсветки и ждём подтверждение
        r, g, b = SPECTRA[self.photo_index]
        self.status_bar.setText(f"Подсветка: {r},{g},{b} (фото {self.photo_index + 1})")

        if not self.arduino.send_and_wait(f"SET {r},{g},{b}", "OK"):
            self.status_bar.setText("❌ Подсветка не включилась")
            self.arduino.close()
            return

        # Делаем снимок через задержку, чтобы свет успел включиться
        QTimer.singleShot(500, self.capture_photo)

    def capture_photo(self):
        """
        Делает снимок с камеры, сохраняет его, сообщает Arduino о завершении,
        и запускает переход к следующему шагу съёмки.
        """
        # Захватываем кадр и сохраняем
        frame = self.camera_widget.get_frame()
        if frame is not None:
            save_photo(frame, self.photo_index)

        # Оповещаем Arduino об окончании съёмки и ждём подтверждение отключения
        if not self.arduino.send_and_wait("PHOTO_DONE", "OFF_DONE"):
            self.status_bar.setText("❌ Подсветка не отключилась")
            self.arduino.close()
            return

        self.photo_index += 1
        QTimer.singleShot(200, self.start_next_photo)

    def delete_photos(self):
        """
        Показывает диалог подтверждения удаления фотографий.
        При подтверждении очищает директорию с фото и обновляет интерфейс.
        """
        reply = QMessageBox.question(self, "Удалить", "Вы уверены, что хотите удалить все фотографии?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            clear_photos()
            self.status_bar.setText("Фотографии удалены")
            self.update_buttons_state()

    def update_buttons_state(self):
        """
        Включает/отключает кнопки в зависимости от наличия фото и подключения Arduino.
        """
        has_photos = len(get_photos()) > 0
        self.photo_btn.setEnabled(self.arduino_available)
        self.gallery_btn.setEnabled(has_photos)
        self.upload_btn.setEnabled(has_photos)
        self.delete_btn.setEnabled(has_photos)

    def disable_all_buttons(self):
        """
        Принудительно отключает все кнопки управления (во время съёмки и загрузки).
        """
        self.photo_btn.setEnabled(False)
        self.gallery_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def show_photos(self):
        """
        Открывает окно просмотра галереи во весь экран.
        """
        self.gallery = GalleryWidget()
        self.gallery.setWindowTitle("📁 Галерея")
        self.gallery.destroyed.connect(lambda: self.activateWindow())
        self.gallery.showFullScreen()

    def upload_photos(self):
        """
        Отправка фотографий: показывает диалог подтверждения отправки и отправляет серию снимков
        """
        reply = QMessageBox.question(self, "Загрузка", "Вы уверены, что хотите выгрузить все фотографии?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.status_bar.setText("Фото отправлены")

    def showEvent(self, event):
        """
        Обработчик события показа окна: активирует кнопки в зависимости от состояния.
        """
        super().showEvent(event)
        self.update_buttons_state()

    def closeEvent(self, event):
        """
        Обработчик закрытия окна: останавливает фоновый поток и закрывает камеру.
        """
        self.arduino_watcher.stop()
        self.camera_widget.close()
        event.accept()
