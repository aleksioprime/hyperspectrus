from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from werkzeug.security import check_password_hash

from db.db import get_db_session
from db.models import User

class LoginDialog(QDialog):
    """
    Диалоговое окно для авторизации пользователя
    """
    def __init__(self):
        super().__init__()
        self.setFixedSize(250, 180)
        self.setWindowTitle("Вход в HyperSpectRus")
        self.user = None

        # --- Основной layout ---
        layout = QVBoxLayout(self)

        # --- Поле логина ---
        self.username = QLineEdit()
        self.username.setPlaceholderText("Логин")
        self.username.setText("user")  # временно (для отладки)
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.username)

        # --- Поле пароля ---
        self.password = QLineEdit()
        self.password.setPlaceholderText("Пароль")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setText("pass")  # временно (для отладки)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password)

        # --- Кнопки ---
        buttons = QHBoxLayout()
        btn_enter = QPushButton("Войти")
        btn_cancel = QPushButton("Выйти")
        buttons.addWidget(btn_enter)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

        # --- Сигналы кнопок ---
        btn_enter.clicked.connect(self.try_login)
        btn_cancel.clicked.connect(self.reject)

        # --- Ставим фокус на логин при запуске ---
        self.username.setFocus()

    def try_login(self):
        """
        Проверяет логин и пароль пользователя.
        Если успех — self.user = User, accept(); если нет — показываем ошибку.
        """
        with get_db_session() as session:
            user = session.query(User).filter_by(username=self.username.text().strip()).first()
        if user and check_password_hash(user.hashed_password, self.password.text()):
            self.user = user
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            self.password.clear()
            self.password.setFocus()

    def keyPressEvent(self, event):
        """
        Обработка нажатия Enter/Return для быстрого логина
        """
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.try_login()
        else:
            super().keyPressEvent(event)
