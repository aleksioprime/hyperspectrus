from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from db.db import SessionLocal
from db.models import User
from werkzeug.security import check_password_hash

class LoginWidget(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success

        layout = QVBoxLayout(self)
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
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
