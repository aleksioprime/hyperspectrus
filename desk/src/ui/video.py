from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QTextEdit, QHBoxLayout, QLineEdit, QGroupBox
from PyQt5.QtGui import QMovie
from src.services.video import VideoStream
from src.ui.firmware import FirmwareWindow

class VideoWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Видеопоток Raspberry Pi")
        self.setFixedSize(900, 600)  # Фиксируем размер окна

        self.init_ui()
        self.video_stream = VideoStream(self.video_label, self.status_text)
        self.video_stream.connect_button = self.connect_button

    def init_ui(self):
        main_layout = QHBoxLayout()  # Разделение на 2 колонки

        # 🎥 Левая часть - видео
        video_layout = QVBoxLayout()

        self.video_label = QLabel("VideoStream")
        self.video_label.setFixedSize(640, 480)

        self.movie = QMovie("src/img/prepare_video.gif")
        self.movie.setScaledSize(self.video_label.size())
        self.video_label.setMovie(self.movie)
        self.movie.start()

        video_layout.addWidget(self.video_label)

        # 🛠️ Правая часть - кнопки и настройки
        control_layout = QVBoxLayout()
        control_layout.setSpacing(15)

        # Кнопка "Обновить прошивку"
        self.firmware_button = QPushButton("Обновить прошивку")
        self.firmware_button.clicked.connect(self.open_firmware_window)
        control_layout.addWidget(self.firmware_button)

        # Поле для ввода IP
        self.ip_input = QLineEdit("192.168.1.100")
        control_layout.addWidget(self.ip_input)

        # Кнопки
        self.connect_button = QPushButton("Подключиться")
        self.connect_button.clicked.connect(self.connect_to_video)
        control_layout.addWidget(self.connect_button)

        self.capture_button = QPushButton("Сохранить стоп-кадр")
        self.capture_button.clicked.connect(self.capture_frame)
        control_layout.addWidget(self.capture_button)

        # Группа "Настройки съёмки"
        settings_group = QGroupBox("Настройки съёмки")
        settings_layout = QVBoxLayout()

        self.resolution_input = QLineEdit("1920x1080")
        settings_layout.addWidget(QLabel("Разрешение:"))
        settings_layout.addWidget(self.resolution_input)

        self.framerate_input = QLineEdit("30 FPS")
        settings_layout.addWidget(QLabel("Частота кадров:"))
        settings_layout.addWidget(self.framerate_input)

        self.apply_settings_button = QPushButton("Применить")
        settings_layout.addWidget(self.apply_settings_button)

        settings_group.setLayout(settings_layout)
        control_layout.addWidget(settings_group)

        control_layout.addStretch()  # Растягиваем элементы вверх

        main_layout.addLayout(video_layout)
        main_layout.addLayout(control_layout)

        # 📜 Строка логов (внизу окна)
        bottom_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        bottom_layout.addWidget(self.status_text)

        # 📦 Основной вертикальный контейнер
        main_vertical_layout = QVBoxLayout()
        main_vertical_layout.addLayout(main_layout)
        main_vertical_layout.addLayout(bottom_layout)

        self.setLayout(main_vertical_layout)

    def connect_to_video(self):
        """Останавливаем анимацию при запуске видеопотока"""
        ip_address = self.ip_input.text().strip()
        if ip_address:
            self.movie.stop()
            self.video_stream.connect_to_video(ip_address)

    def capture_frame(self):
        """Вызывает метод capture_frame у video_stream"""
        if hasattr(self, "video_stream"):
            self.video_stream.capture_frame()

    def open_firmware_window(self):
        """Открывает окно прошивки в модальном режиме"""
        firmware_window = FirmwareWindow(parent=self)
        firmware_window.exec_()
