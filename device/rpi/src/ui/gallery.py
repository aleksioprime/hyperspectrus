from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize

from services.photo import get_photos
from config.settings import icon_path


class GalleryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Галерея")
        self.setFixedSize(480, 320)
        self.setStyleSheet("font-size: 18px;")

        self.photos = get_photos()
        self.index = 0

        # Изображение
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(480, 240)

        # Счётчик
        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignCenter)

        # Кнопки
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

        # Нижний ряд: ◀️ [Фото 1/5] ▶️
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.counter_label)
        nav_layout.addWidget(self.next_btn)

        # Верхний ряд: [🔙]
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.back_btn)
        top_layout.addStretch()

        # Основной layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addLayout(top_layout)
        layout.addWidget(self.image_label)
        layout.addLayout(nav_layout)
        self.setLayout(layout)

        self.update_image()

    def update_image(self):
        """
        Обновляет изображение на экране в соответствии с текущим индексом.
        Если фотографий нет — отображает сообщение.
        """
        if not self.photos:
            self.image_label.setText("Нет фото")
            self.counter_label.setText("")
            return

        photo_path = self.photos[self.index]
        pixmap = QPixmap(photo_path).scaled(
            self.image_label.width(), self.image_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)
        self.counter_label.setText(f"Фото {self.index + 1} / {len(self.photos)}")

    def show_previous(self):
        """
        Показывает предыдущее фото, если индекс больше нуля.
        Обновляет картинку и счётчик.
        """
        if self.index > 0:
            self.index -= 1
            self.update_image()

    def show_next(self):
        """
        Показывает следующее фото, если оно есть.
        Обновляет картинку и счётчик.
        """
        if self.index < len(self.photos) - 1:
            self.index += 1
            self.update_image()
