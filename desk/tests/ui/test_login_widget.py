import pytest
from PyQt6.QtWidgets import QDialog, QPushButton # For DialogCode
from PyQt6.QtCore import Qt # For Qt.MouseButton if needed by qtbot.mouseClick
from unittest.mock import patch # For mocking QMessageBox

from desk.src.ui.login_widget import LoginDialog
from desk.src.db.models import User
from werkzeug.security import generate_password_hash

# The db_session fixture is automatically available from desk/tests/conftest.py

TEST_USER = "testuser"
TEST_PASSWORD = "password123"

@pytest.fixture
def test_user_in_db(db_session):
    """Fixture to create a test user in the database."""
    hashed_pw = generate_password_hash(TEST_PASSWORD)
    user = User(
        username=TEST_USER,
        hashed_password=hashed_pw,
        email=f"{TEST_USER}@example.com",
        first_name="Test",
        last_name="UserLogin"
    )
    db_session.add(user)
    db_session.commit()
    return user

def test_login_dialog_successful_login(qtbot, db_session, test_user_in_db):
    """Test successful login with correct credentials."""
    dialog = LoginDialog()
    qtbot.addWidget(dialog) # Register dialog with qtbot

    dialog.username.setText(TEST_USER)
    dialog.password.setText(TEST_PASSWORD)

    dialog.try_login() # Directly call the login logic

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.user is not None
    assert dialog.user.username == TEST_USER

def test_login_dialog_incorrect_password(qtbot, db_session, test_user_in_db):
    """Test login attempt with incorrect password."""
    dialog = LoginDialog()
    qtbot.addWidget(dialog)

    dialog.username.setText(TEST_USER)
    dialog.password.setText("wrongpassword")

    with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        dialog.try_login()

    mock_warning.assert_called_once()
    args, _ = mock_warning.call_args
    assert "Неверный логин или пароль" in args[1] # Check message content
    
    assert dialog.user is None
    assert dialog.result() != QDialog.DialogCode.Accepted # Should not be accepted

def test_login_dialog_user_not_found(qtbot, db_session): # No test_user_in_db fixture here
    """Test login attempt with a username that does not exist."""
    dialog = LoginDialog()
    qtbot.addWidget(dialog)

    dialog.username.setText("nonexistentuser")
    dialog.password.setText("anypassword")

    with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        dialog.try_login()

    mock_warning.assert_called_once()
    args, _ = mock_warning.call_args
    assert "Неверный логин или пароль" in args[1]

    assert dialog.user is None
    assert dialog.result() != QDialog.DialogCode.Accepted

def test_login_dialog_cancel_action(qtbot):
    """Test cancelling the login dialog."""
    dialog = LoginDialog()
    qtbot.addWidget(dialog)

    # Simulate pressing the "Отмена" button by calling reject() directly
    # as the button itself is connected to self.reject
    dialog.reject()

    assert dialog.result() == QDialog.DialogCode.Rejected

def test_login_dialog_empty_credentials_shows_warning(qtbot, db_session):
    """Test that attempting to login with empty credentials shows a warning."""
    dialog = LoginDialog()
    qtbot.addWidget(dialog)

    dialog.username.setText("")
    dialog.password.setText("")

    with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        dialog.try_login()
    
    mock_warning.assert_called_once()
    args, _ = mock_warning.call_args
    assert "Неверный логин или пароль" in args[1] # Or a more specific message if implemented

    assert dialog.user is None
    assert dialog.result() != QDialog.DialogCode.Accepted

def test_login_dialog_key_press_enter_triggers_login(qtbot, db_session, test_user_in_db):
    """Test that pressing Enter key triggers login attempt."""
    dialog = LoginDialog()
    qtbot.addWidget(dialog)

    dialog.username.setText(TEST_USER)
    dialog.password.setText(TEST_PASSWORD)
    
    # Simulate Enter key press on the dialog or a specific widget
    # For simplicity, we'll patch try_login and check if it's called
    # A more direct way is qtbot.keyPress(dialog, Qt.Key.Key_Return)
    
    with patch.object(dialog, 'try_login') as mock_try_login:
        qtbot.keyPress(dialog.password, Qt.Key.Key_Return) # Press Enter on password field
    
    mock_try_login.assert_called_once()

    # To verify actual login success, we can't just mock try_login.
    # Let's do a full check:
    dialog_full_check = LoginDialog()
    qtbot.addWidget(dialog_full_check)
    dialog_full_check.username.setText(TEST_USER)
    dialog_full_check.password.setText(TEST_PASSWORD)

    qtbot.keyPress(dialog_full_check.password, Qt.Key.Key_Return)
    
    assert dialog_full_check.result() == QDialog.DialogCode.Accepted
    assert dialog_full_check.user is not None
    assert dialog_full_check.user.username == TEST_USER
