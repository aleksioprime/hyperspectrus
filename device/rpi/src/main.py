from PyQt5.QtWidgets import QApplication
from ui.main import CameraApp
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CameraApp()
    win.showFullScreen()
    sys.exit(app.exec_())