import sys
from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow

from src.ui.video import VideoWindow
from src.ui.research import ResearchWindow


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("src/forms/main.ui", self)

        self.actionShoot.triggered.connect(self.open_video_window)
        self.actionResearch.triggered.connect(self.open_research_window)
        self.actionExit.triggered.connect(self.close)

        # Создаём и сразу показываем VideoWindow
        self.video_window = VideoWindow()
        self.video_window.show()

        self.research_window = None

        # Главное окно скрываем
        QTimer.singleShot(0, self.hide)

    def open_video_window(self):
        if self.video_window is None:
            self.video_window = VideoWindow()

        self.video_window.show()
        self.research_window.hide()

    def open_research_window(self):
        if self.research_window is None:
            self.research_window = ResearchWindow()

        self.research_window.show()
        self.video_window.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())
