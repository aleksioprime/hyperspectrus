from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
)

class UserProfileDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Профиль пользователя")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Username
        self.username_label = QLabel("Имя пользователя:")
        self.username_input = QLineEdit(self.user.username)
        self.username_input.setReadOnly(True)
        form_layout.addRow(self.username_label, self.username_input)

        # First Name
        self.first_name_label = QLabel("Имя:")
        self.first_name_input = QLineEdit(self.user.first_name if self.user.first_name else "N/A")
        self.first_name_input.setReadOnly(True)
        form_layout.addRow(self.first_name_label, self.first_name_input)

        # Last Name
        self.last_name_label = QLabel("Фамилия:")
        self.last_name_input = QLineEdit(self.user.last_name if self.user.last_name else "N/A")
        self.last_name_input.setReadOnly(True)
        form_layout.addRow(self.last_name_label, self.last_name_input)

        # Email
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit(self.user.email)
        self.email_input.setReadOnly(True)
        form_layout.addRow(self.email_label, self.email_input)
        
        # Superuser status - Bonus, but good to have
        self.is_superuser_label = QLabel("Суперпользователь:")
        self.is_superuser_input = QLineEdit("Да" if self.user.is_superuser else "Нет")
        self.is_superuser_input.setReadOnly(True)
        form_layout.addRow(self.is_superuser_label, self.is_superuser_input)


        main_layout.addLayout(form_layout)

        # OK Button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        main_layout.addWidget(self.ok_button)

        self.setLayout(main_layout)
        # Adjust size to fit content
        self.adjustSize()
