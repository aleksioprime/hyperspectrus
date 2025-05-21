import cv2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

class CameraWidget(QWidget):
    """
    Видеовиджет камеры: отображает поток, выдает текущий кадр.
    """
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Камера не найдена")
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Прижать вверх и по центру
        self.label.setScaledContents(False)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """
        Считывает кадр и выводит в label.
        """
        ret, frame = self.cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img).scaled(
                self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label.setPixmap(pixmap)

    def get_frame(self):
        """
        Возвращает текущий кадр (numpy array) с камеры.
        """
        ret, frame = self.cap.read()
        return frame if ret else None

    def close(self):
        self.timer.stop()
        self.cap.release()
