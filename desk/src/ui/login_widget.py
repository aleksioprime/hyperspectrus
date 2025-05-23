from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
from PyQt6.QtCore import Qt
from werkzeug.security import check_password_hash

from db.db import get_db_session
from db.models import User

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(250, 180)
        self.setWindowTitle("Вход в HyperSpectRus")
        self.user = None  # Сохраним пользователя после успешного входа

        layout = QVBoxLayout(self)
        self.username = QLineEdit()
        self.username.setText("user") # временно
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setText("pass") # временно
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.username)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password)

        buttons = QHBoxLayout()
        btn_enter = QPushButton("Войти")
        buttons.addWidget(btn_enter)
        btn_cancel = QPushButton("Отмена")
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)
        btn_enter.clicked.connect(self.try_login)
        btn_cancel.clicked.connect(self.reject)  # Закрывает окно с кодом Cancel

    def try_login(self):
        with get_db_session() as session:
            user = session.query(User).filter_by(username=self.username.text()).first()
        if user and check_password_hash(user.hashed_password, self.password.text()):
            self.user = user  # сохраняем объект пользователя
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.try_login()
