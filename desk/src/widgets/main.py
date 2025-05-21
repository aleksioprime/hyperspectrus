from PyQt6.QtWidgets import QMainWindow, QWidget, QStackedWidget
from widgets.login import LoginWidget
from widgets.patients.main import PatientsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HyperSpectRus v0.0.1")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login = LoginWidget(self.login_success)
        self.stack.addWidget(self.login)

    def login_success(self, user):
        self.user = user
        self.patients = PatientsWidget(user)
        self.stack.addWidget(self.patients)
        self.stack.setCurrentWidget(self.patients)
        self.center_window_on_screen(self)

    def center_window_on_screen(self, window):
        screen = window.screen().availableGeometry()
        size = window.frameGeometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        window.move(x, y)