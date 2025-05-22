import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from db.db import init_db


def center_window_on_screen(window):
    screen = window.screen().availableGeometry()
    size = window.frameGeometry()
    x = (screen.width() - size.width()) // 2
    y = (screen.height() - size.height()) // 2
    window.move(x, y)

def main():
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    center_window_on_screen(win)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()