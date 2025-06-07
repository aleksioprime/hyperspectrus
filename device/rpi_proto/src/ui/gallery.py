from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from services.photo import get_photos_for_task
from config.settings import icon_path
import os

"""
Виджет галереи для просмотра фото выбранной задачи.
"""

class GalleryWidget(QWidget):
    """
    Окно галереи для просмотра фото по задаче.
    """
    def __init__(self, task_id):
        super().__init__()
        self.setWindowTitle("Галерея")
        self.setStyleSheet("font-size: 18px;")
        self.task_id = task_id
        self.photos = get_photos_for_task(task_id)
        self.index = 0

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignCenter)

        self.filename_label = QLabel()
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setStyleSheet("font-size: 14px; color: #666;")

        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(QIcon(icon_path("left.png")))
        self.prev_btn.setIconSize(QSize(32, 32))
        self.prev_btn.setFixedSize(60, 40)
        self.prev_btn.clicked.connect(self.show_previous)

        self.next_btn = QPushButton()
        self.next_btn.setIcon(QIcon(icon_path("right.png")))
        self.next_btn.setIconSize(QSize(32, 32))
        self.next_btn.setFixedSize(60, 40)
        self.next_btn.clicked.connect(self.show_next)

        self.back_btn = QPushButton()
        self.back_btn.setIcon(QIcon(icon_path("return.png")))
        self.back_btn.setIconSize(QSize(32, 32))
        self.back_btn.setFixedSize(60, 40)
        self.back_btn.clicked.connect(self.close)

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.counter_label)
        nav_layout.addWidget(self.next_btn)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.back_btn)
        top_layout.addStretch()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addLayout(top_layout)
        layout.addWidget(self.image_label)
        layout.addWidget(self.filename_label)
        layout.addLayout(nav_layout)
        self.setLayout(layout)
        self.update_image()

    def update_image(self):
        """
        Показывает фото по индексу и название файла.
        Отключает кнопки, если фото отсутствуют или один кадр.
        """
        total = len(self.photos)
        if not self.photos:
            self.image_label.setText("Нет фото")
            self.counter_label.setText("")
            self.filename_label.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        # Убедимся, что индекс в допустимом диапазоне
        self.index = min(max(0, self.index), total - 1)
        photo_path = self.photos[self.index]

        # Проверим, что файл реально существует (мог быть удалён)
        if not os.path.isfile(photo_path):
            self.image_label.setText("Файл не найден")
            self.filename_label.setText(photo_path)
        else:
            pixmap = QPixmap(photo_path).scaled(
                self.image_label.width(), self.image_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
            self.filename_label.setText(os.path.basename(photo_path))
        self.counter_label.setText(f"Фото {self.index + 1} / {total}")

        # Кнопки влево-вправо
        self.prev_btn.setEnabled(self.index > 0)
        self.next_btn.setEnabled(self.index < total - 1)

    def show_previous(self):
        if self.index > 0:
            self.index -= 1
            self.update_image()

    def show_next(self):
        if self.index < len(self.photos) - 1:
            self.index += 1
            self.update_image()
