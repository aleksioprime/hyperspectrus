from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QTextEdit, QHBoxLayout, QLineEdit

from src.services.video import VideoStream

class VideoWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Видеопоток Raspberry Pi")
        self.setGeometry(100, 100, 800, 500)

        self.init_ui()
        self.video_stream = VideoStream(self.video_label, self.status_text)
        self.video_stream.connect_button = self.connect_button

    def init_ui(self):
        layout = QVBoxLayout()

        self.video_label = QLabel("")
        self.video_label.setFixedSize(640, 480)
        layout.addWidget(self.video_label)

        # 🔹 Поле для ввода IP-адреса
        self.ip_input = QLineEdit("192.168.1.100")  # Значение по умолчанию
        layout.addWidget(self.ip_input)

        video_buttons = QHBoxLayout()

        # 🔹 Кнопка подключения
        self.connect_button = QPushButton("Подключиться")
        self.connect_button.clicked.connect(self.connect_to_video)  # Используем метод
        video_buttons.addWidget(self.connect_button)

        # 🔹 Кнопка сохранения кадра
        self.capture_button = QPushButton("Сохранить стоп-кадр")
        self.capture_button.clicked.connect(self.capture_frame)
        video_buttons.addWidget(self.capture_button)

        layout.addLayout(video_buttons)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        self.setLayout(layout)

    def connect_to_video(self):
        """Получает IP-адрес из поля и подключается к видеопотоку"""
        ip_address = self.ip_input.text().strip()
        if ip_address:
            self.video_stream.connect_to_video(ip_address)

    def capture_frame(self):
        """Вызывает метод capture_frame у video_stream"""
        if hasattr(self, "video_stream"):
            self.video_stream.capture_frame()
