from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
)
from werkzeug.security import generate_password_hash
from db.db import get_db_session
from db.models import User


class CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create Initial Superuser")

        # Layouts
        layout = QVBoxLayout(self)
        form_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        # Username
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)

        # Password
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)

        # Confirm Password
        self.confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.confirm_password_label)
        form_layout.addWidget(self.confirm_password_input)

        # First Name
        self.first_name_label = QLabel("First Name:")
        self.first_name_input = QLineEdit()
        form_layout.addWidget(self.first_name_label)
        form_layout.addWidget(self.first_name_input)

        # Last Name
        self.last_name_label = QLabel("Last Name:")
        self.last_name_input = QLineEdit()
        form_layout.addWidget(self.last_name_label)
        form_layout.addWidget(self.last_name_input)

        # Email
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        form_layout.addWidget(self.email_label)
        form_layout.addWidget(self.email_input)

        # Buttons
        self.create_user_button = QPushButton("Create User")
        self.cancel_button = QPushButton("Cancel")

        self.create_user_button.clicked.connect(self.create_user)
        self.cancel_button.clicked.connect(self.reject)  # QDialog.reject()

        button_layout.addWidget(self.create_user_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

    def create_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()

        # Validation
        if not all([username, password, confirm_password, first_name, last_name, email]):
            QMessageBox.warning(self, "Validation Error", "All fields must be filled.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            return

        if "@" not in email:
            QMessageBox.warning(self, "Validation Error", "Invalid email address.")
            return

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create user
        db_session = get_db_session()
        new_user = User(
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_superuser=True,
            is_active=True,
        )
        db_session.add(new_user)
        try:
            db_session.commit()
            self.accept()  # QDialog.accept()
        except Exception as e:
            db_session.rollback()
            QMessageBox.critical(self, "Database Error", f"Could not create user: {e}")
        finally:
            db_session.close()

if __name__ == '__main__':
    # This is for testing purposes only
    from PyQt6.QtWidgets import QApplication
    import sys

    # Mock db.db and db.models for standalone testing if they don't exist
    # or have dependencies that are not available in this context.
    class MockUser:
        def __init__(self, username, hashed_password, first_name, last_name, email, is_superuser, is_active):
            self.username = username
            self.hashed_password = hashed_password
            self.first_name = first_name
            self.last_name = last_name
            self.email = email
            self.is_superuser = is_superuser
            self.is_active = is_active
            print(f"MockUser created: {self.__dict__}")

    class MockDbSession:
        def add(self, obj):
            print(f"MockDbSession: Adding {obj.__class__.__name__} - {obj.username}")
        def commit(self):
            print("MockDbSession: Committing changes")
        def rollback(self):
            print("MockDbSession: Rolling back changes")
        def close(self):
            print("MockDbSession: Closing session")

    # Replace actual db interactions with mocks if not running in full app context
    original_get_db_session = get_db_session
    original_User = User

    def mock_get_db_session():
        return MockDbSession()

    # Apply mocks
    get_db_session = mock_get_db_session
    User = MockUser


    app = QApplication(sys.argv)
    dialog = CreateUserDialog()
    if dialog.exec():
        print("User creation accepted.")
    else:
        print("User creation cancelled.")

    # Restore original functions if necessary, though for a test script exit it might not matter
    get_db_session = original_get_db_session
    User = original_User
    sys.exit(app.exec())
