from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QTextEdit

from src.services.firmware import FirmwareUploader


class FirmwareWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Обновление прошивки Raspberry Pi")
        self.setGeometry(100, 100, 400, 300)

        self.init_ui()

        self.firmware_uploader = FirmwareUploader(self.status_text)

        self.file_button.clicked.connect(self.firmware_uploader.select_file)
        self.upload_button.clicked.connect(lambda: self.firmware_uploader.upload_file(self.ip_input.text()))

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
