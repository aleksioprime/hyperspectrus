from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class CameraWidget(QWidget):
    def __init__(self, device_ip=None):
        super().__init__()
        layout = QVBoxLayout(self)
        self.label = QLabel("Поток камеры")
        layout.addWidget(self.label)
        self.capture_btn = QPushButton("Сделать серию снимков")
        layout.addWidget(self.capture_btn)
        self.capture_btn.clicked.connect(self.capture_series)
        self.device_ip = device_ip
        self.cap = None

    def start_camera(self):
        pass

    def capture_series(self):
        # Аналогично как делал выше — снять серию фото
        pass

    def save_series(self):
        # Сохранить файлы, привязать к сессии в БД
        pass
