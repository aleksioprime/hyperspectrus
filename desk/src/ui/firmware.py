from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QLineEdit, QTextEdit, QApplication

from src.services.firmware import FirmwareUploader


class FirmwareWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Обновление прошивки Raspberry Pi")
        self.setGeometry(0, 0, 400, 300)

        self.init_ui()
        self.firmware_uploader = FirmwareUploader(self.status_text)

        self.file_button.clicked.connect(self.firmware_uploader.select_file)
        self.upload_button.clicked.connect(lambda: self.firmware_uploader.upload_file(self.ip_input.text()))

        self.center_window()

    def init_ui(self):
        layout = QVBoxLayout()

        self.ip_label = QLabel("IP Raspberry:")
        self.ip_input = QLineEdit("192.168.1.100")
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_input)

        self.file_button = QPushButton("Выбрать прошивку (Python-скрипт)")
        layout.addWidget(self.file_button)

        self.upload_button = QPushButton("Загрузить прошивку")
        layout.addWidget(self.upload_button)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        self.setLayout(layout)

    def center_window(self):
        """Центрирование окна относительно главного окна"""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen_rect = QApplication.desktop().screenGeometry()
            x = (screen_rect.width() - self.width()) // 2
            y = (screen_rect.height() - self.height()) // 2
            self.move(x, y)
