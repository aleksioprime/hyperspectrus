import os
os.environ['LIBGL_DEBUG'] = 'quiet'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui.main import CameraApp
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOverrideCursor(Qt.BlankCursor)
    win = CameraApp()
    win.showFullScreen()
    sys.exit(app.exec_())