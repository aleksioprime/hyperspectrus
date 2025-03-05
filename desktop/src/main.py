import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

from src.ui.video import VideoWindow
from src.ui.firmware import FirmwareWindow


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Raspberry Manager")
        self.setGeometry(100, 100, 400, 200)

        central_widget = QWidget()
        layout = QVBoxLayout()

        self.video_button = QPushButton("📹 Открыть видеопоток")
        self.video_button.clicked.connect(self.open_video_window)
        layout.addWidget(self.video_button)

        self.firmware_button = QPushButton("🔧 Настройки прошивки")
        self.firmware_button.clicked.connect(self.open_firmware_window)
        layout.addWidget(self.firmware_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.video_window = None
        self.firmware_window = None

    def open_video_window(self):
        if self.video_window is None or not self.video_window.isVisible():
            self.video_window = VideoWindow()
            self.video_window.show()

    def open_firmware_window(self):
        if self.firmware_window is None:
            self.firmware_window = FirmwareWindow()
        self.firmware_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
