"""Виджет отображения камеры для Raspberry Pi.

Использует библиотеку picamera2 для работы с камерой через CSI-порт.
"""

from picamera2 import Picamera2
import cv2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap


class CameraWidget(QWidget):
    """Видеовиджет камеры: показывает поток и предоставляет кадры."""

    def __init__(self):
        super().__init__()
        # Инициализируем камеру и запускаем предварительный просмотр
        self.picam2 = Picamera2()

        self.preview_config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 360)}
        )
        self.capture_config = self.picam2.create_still_configuration(
            main={"format": "RGB888", "size": (1920, 1080)}  # подставь своё max
        )
        self.picam2.configure(self.preview_config)
        self.picam2.start()

        # Виджет для отображения кадров
        self.label = QLabel()
        # Прижимаем изображение к верху и по центру
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label.setScaledContents(False)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 6, 0, 6)
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
            rgb = frame[..., ::-1]
            h, w, ch = rgb.shape
            img = QImage(rgb.tobytes(), w, h, ch * w, QImage.Format_RGB888)

            # crop=True — "cover", crop=False — стандартное поведение
            pixmap = self.make_pixmap(self.label, img, mode = "height")
            self.label.setPixmap(pixmap)

    def make_pixmap(self, label: QLabel, img: QImage, mode: str = "cover") -> QPixmap:
        """
        Масштабирует изображение под label.
        mode:
        - "cover"  : Заполнение по ширине, обрезка по высоте (default)
        - "contain": Вписать полностью без обрезки (KeepAspectRatio)
        - "width"  : Растянуть по ширине, центрировать и обрезать по высоте
        - "height" : Растянуть по высоте, центрировать и обрезать по ширине
        """
        label_width = label.width()
        label_height = label.height()
        img_width = img.width()
        img_height = img.height()

        if mode == "cover" or mode == "width":
            scale_factor = label_width / img_width
            new_height = int(img_height * scale_factor)
            scaled_img = img.scaled(label_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            if new_height > label_height:
                y_offset = (new_height - label_height) // 2
                pixmap = QPixmap.fromImage(scaled_img).copy(0, y_offset, label_width, label_height)
            else:
                pixmap = QPixmap.fromImage(scaled_img)
        elif mode == "height":
            scale_factor = label_height / img_height
            new_width = int(img_width * scale_factor)
            scaled_img = img.scaled(new_width, label_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            if new_width > label_width:
                x_offset = (new_width - label_width) // 2
                pixmap = QPixmap.fromImage(scaled_img).copy(x_offset, 0, label_width, label_height)
            else:
                pixmap = QPixmap.fromImage(scaled_img)
        elif mode == "contain":
            scaled_img = img.scaled(label_width, label_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pixmap = QPixmap.fromImage(scaled_img)
        else:
            # Fallback — обычное поведение
            scaled_img = img.scaled(label_width, label_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pixmap = QPixmap.fromImage(scaled_img)
        return pixmap

    def get_preview_frame(self):
        """Всегда возвращает кадр маленького разрешения."""
        return self.picam2.capture_array()

    def get_frame(self, highres=False):
        """
        Возвращает кадр. Если highres=True, временно переключается на highres.
        Никогда не выводит highres в интерфейс!
        """
        if highres:
            self.picam2.stop()
            self.picam2.configure(self.capture_config)
            self.picam2.start()
            frame = self.picam2.capture_array()
            self.picam2.stop()
            self.picam2.configure(self.preview_config)
            self.picam2.start()
        else:
            frame = self.get_preview_frame()
        return frame

    def close(self):
        """Останавливает камеру и освобождает ресурсы."""
        self.timer.stop()
        self.picam2.close()
