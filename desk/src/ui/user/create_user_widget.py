from werkzeug.security import generate_password_hash
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt

from db.db import get_db_session
from db.models import User


class CreateUserDialog(QDialog):
    """
    Диалоговое окно для создания нового пользователя или администратора
    """

    def __init__(self, parent=None, is_creating_superuser=True):
        super().__init__(parent)
        self.is_creating_superuser = is_creating_superuser

        # Фиксированный размер окна
        self.setFixedSize(330, 270)
        self.setWindowTitle(
            "Создание администратора" if self.is_creating_superuser else "Создание пользователя"
        )

        # --- Основной layout ---
        main_layout = QVBoxLayout(self)

        # --- Форма полей ---
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.username_input = QLineEdit()
        self.username_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addRow("Логин:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addRow("Пароль:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addRow("Подтвердите пароль:", self.confirm_password_input)

        self.first_name_input = QLineEdit()
        self.first_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addRow("Имя:", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addRow("Фамилия:", self.last_name_input)

        self.email_input = QLineEdit()
        form_layout.addRow("E-mail:", self.email_input)
        self.email_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        main_layout.addLayout(form_layout)

        # --- Кнопки ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.create_user_button = QPushButton("Создать")
        self.cancel_button = QPushButton("Отмена")
        self.create_user_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.cancel_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        button_layout.addWidget(self.create_user_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        # --- Сигналы ---
        self.create_user_button.clicked.connect(self.create_user)
        self.cancel_button.clicked.connect(self.reject)

    def create_user(self):
        """
        Создаёт пользователя после проверки всех полей
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()

        # Проверки
        if not all([username, password, confirm_password, first_name, last_name, email]):
            QMessageBox.warning(self, "Ошибка валидации", "Пожалуйста, заполните все поля.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Ошибка валидации", "Введённые пароли не совпадают.")
            return

        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Ошибка валидации", "Пожалуйста, введите корректный адрес электронной почты.")
            return

        if len(username) < 3:
            QMessageBox.warning(self, "Ошибка валидации", "Логин должен содержать не менее 3 символов.")
            return
        if len(password) < 4:
            QMessageBox.warning(self, "Ошибка валидации", "Пароль должен содержать не менее 6 символов.")
            return

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        with get_db_session() as db_session:
            # Проверяем уникальность логина и email
            if db_session.query(User).filter_by(username=username).first():
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует.")
                return
            if db_session.query(User).filter_by(email=email).first():
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким E-mail уже существует.")
                return

            new_user = User(
                username=username,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_superuser=self.is_creating_superuser,
                is_active=True,
            )
            db_session.add(new_user)
            db_session.commit()
            QMessageBox.information(self, "Успешно", "Пользователь успешно создан.")
            self.accept()
