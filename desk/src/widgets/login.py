from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from werkzeug.security import check_password_hash

from db.db import SessionLocal
from db.models import User


class LoginWidget(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success

        layout = QVBoxLayout(self)
        self.username = QLineEdit()
        self.username.setText("user") # временно
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setText("pass") # временно
        btn = QPushButton("Войти")
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.username)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password)
        layout.addWidget(btn)
        btn.clicked.connect(self.try_login)

    def try_login(self):
        session = SessionLocal()
        user = session.query(User).filter_by(username=self.username.text()).first()
        if user and check_password_hash(user.hashed_password, self.password.text()):
            self.on_login_success(user)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.try_login()
