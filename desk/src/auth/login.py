from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
import api.cloud

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход")
        layout = QVBoxLayout(self)
        self.login_input = QLineEdit(); self.login_input.setPlaceholderText("Логин")
        self.pass_input = QLineEdit(); self.pass_input.setPlaceholderText("Пароль"); self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        login_btn = QPushButton("Войти")
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.pass_input)
        layout.addWidget(login_btn)
        login_btn.clicked.connect(self.do_login)

    def do_login(self):
        username = self.login_input.text()
        password = self.pass_input.text()
        try:
            api.cloud.login_cloud(username, password)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось войти:\n{e}")
