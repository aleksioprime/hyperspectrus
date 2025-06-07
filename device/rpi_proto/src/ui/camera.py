"""Виджет отображения камеры для Raspberry Pi.

Использует библиотеку picamera2 для работы с камерой через CSI-порт.
"""

from picamera2 import Picamera2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap


class CameraWidget(QWidget):
    """Видеовиджет камеры: показывает поток и предоставляет кадры."""

    def __init__(self):
        super().__init__()
        # Инициализируем камеру и запускаем предварительный просмотр
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
        self.picam2.configure(config)
        self.picam2.start()

        # Виджет для отображения кадров
        self.label = QLabel()
        # Прижимаем изображение к верху и по центру
        self.label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.label.setScaledContents(False)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Таймер периодически обновляет кадр
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """Считывает кадр с камеры и выводит его на экран."""
        frame = self.picam2.capture_array()
        if frame is not None:
            h, w, ch = frame.shape
            img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img).scaled(
                self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label.setPixmap(pixmap)

    def get_frame(self):
        """Возвращает текущий кадр камеры в виде numpy-массива."""
        return self.picam2.capture_array()

    def close(self):
        """Останавливает камеру и освобождает ресурсы."""
        self.timer.stop()
        self.picam2.close()
