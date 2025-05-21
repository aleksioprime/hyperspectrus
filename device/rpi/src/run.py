import os
os.environ['LIBGL_DEBUG'] = 'quiet'
import sys
import threading

from models.db import init_db

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from ui.main import CameraApp

import signal

def handle_sigint(*args):
    QApplication.quit()

signal.signal(signal.SIGINT, handle_sigint)

def start_api():
    """
    Запускает FastAPI-сервер в отдельном потоке.
    """
    import uvicorn
    from api.server import app
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

if __name__ == "__main__":

    init_db()
    # Стартуем API сервер в фоне
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    # Стартуем PyQt-приложение
    app = QApplication(sys.argv)
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)
    app.setOverrideCursor(Qt.BlankCursor)
    win = CameraApp()
    win.showFullScreen()
    sys.exit(app.exec_())
