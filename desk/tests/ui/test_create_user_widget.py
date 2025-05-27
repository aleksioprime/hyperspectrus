import pytest

from PyQt6.QtWidgets import QDialog, QMessageBox
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from src.ui.user.create_user_widget import CreateUserDialog
from src.db.models import User


# db_session fixture from conftest.py will be used

# Helper function to fill dialog fields
def _fill_dialog(dialog, username, pw1, pw2, first, last, email):
    dialog.username_input.setText(username)
    dialog.password_input.setText(pw1)
    dialog.confirm_password_input.setText(pw2)
    dialog.first_name_input.setText(first)
    dialog.last_name_input.setText(last)
    dialog.email_input.setText(email)

def test_create_superuser_successful(qtbot, db_session):
    dialog = CreateUserDialog(is_creating_superuser=True)
    qtbot.addWidget(dialog)

    _fill_dialog(dialog, "supertest", "pass123", "pass123", "Super", "User", "super@example.com")

    # The dialog's create_user uses its own session, so we can't directly mock get_db_session easily
    # unless we monkeypatch it globally for this test.
    # For now, we'll let it run and check results.
    dialog.create_user()

    assert dialog.result() == QDialog.DialogCode.Accepted

    user = db_session.query(User).filter_by(username="supertest").first()
    assert user is not None
    assert user.email == "super@example.com"
    assert user.is_superuser is True
    assert user.is_active is True
    assert check_password_hash(user.hashed_password, "pass123")

def test_create_regular_user_successful(qtbot, db_session):
    dialog = CreateUserDialog(is_creating_superuser=False)
    qtbot.addWidget(dialog)

    _fill_dialog(dialog, "regtest", "pass123", "pass123", "Regular", "User", "reg@example.com")
    dialog.create_user()

    assert dialog.result() == QDialog.DialogCode.Accepted

    user = db_session.query(User).filter_by(username="regtest").first()
    assert user is not None
    assert user.email == "reg@example.com"
    assert user.is_superuser is False
    assert user.is_active is True
    assert check_password_hash(user.hashed_password, "pass123")

def test_create_user_password_mismatch(qtbot, db_session):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    _fill_dialog(dialog, "mismatchuser", "pass123", "pass456", "Mismatch", "Pass", "mismatch@example.com")

    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.create_user()

    mock_warning.assert_called_once()
    args, _ = mock_warning.call_args
    assert "Passwords do not match" in args[1] # Check message content
    assert dialog.result() != QDialog.DialogCode.Accepted

    user = db_session.query(User).filter_by(username="mismatchuser").first()
    assert user is None

def test_create_user_empty_field_username(qtbot, db_session):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    _fill_dialog(dialog, "", "pass123", "pass123", "Empty", "User", "empty@example.com")

    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.create_user()

    mock_warning.assert_called_once()
    args, _ = mock_warning.call_args
    assert "All fields must be filled" in args[1]
    assert dialog.result() != QDialog.DialogCode.Accepted

    user = db_session.query(User).filter_by(email="empty@example.com").first()
    assert user is None

def test_create_user_empty_field_email(qtbot, db_session):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    _fill_dialog(dialog, "emptyemailuser", "pass123", "pass123", "Empty", "Email", "")

    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.create_user()

    mock_warning.assert_called_once()
    args, _ = mock_warning.call_args
    assert "All fields must be filled" in args[1] # Or "Invalid email address" if it hits that first
    assert dialog.result() != QDialog.DialogCode.Accepted

    user = db_session.query(User).filter_by(username="emptyemailuser").first()
    assert user is None

def test_create_user_invalid_email(qtbot, db_session):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    _fill_dialog(dialog, "invalidemailuser", "pass123", "pass123", "Invalid", "Email", "invalidemail")

    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.create_user()

    mock_warning.assert_called_once()
    args, _ = mock_warning.call_args
    assert "Invalid email address" in args[1]
    assert dialog.result() != QDialog.DialogCode.Accepted

    user = db_session.query(User).filter_by(username="invalidemailuser").first()
    assert user is None


def test_create_user_duplicate_username(qtbot, db_session):
    # Create initial user directly
    existing_user = User(username="existinguser", email="exists_user@example.com", hashed_password="pw")
    db_session.add(existing_user)
    db_session.commit()

    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)
    _fill_dialog(dialog, "existinguser", "pass123", "pass123", "Dup", "User", "new_dup_user@example.com")

    # The dialog's create_user catches IntegrityError and shows QMessageBox.critical
    with patch.object(QMessageBox, 'critical') as mock_critical:
        dialog.create_user()

    mock_critical.assert_called_once()
    args, _ = mock_critical.call_args
    assert "Could not create user" in args[1] # Check message content
    assert dialog.result() != QDialog.DialogCode.Accepted

def test_create_user_duplicate_email(qtbot, db_session):
    # Create initial user directly
    existing_user = User(username="anotheruser_dup_email", email="existing_email@example.com", hashed_password="pw")
    db_session.add(existing_user)
    db_session.commit()

    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)
    _fill_dialog(dialog, "newuser_dup_email", "pass123", "pass123", "Dup", "Email", "existing_email@example.com")

    with patch.object(QMessageBox, 'critical') as mock_critical:
        dialog.create_user()

    mock_critical.assert_called_once()
    args, _ = mock_critical.call_args
    assert "Could not create user" in args[1]
    assert dialog.result() != QDialog.DialogCode.Accepted

def test_create_user_dialog_cancel_action(qtbot):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    dialog.reject() # Simulate cancel button click

    assert dialog.result() == QDialog.DialogCode.Rejected
    # No need to check DB as no attempt to create user was made.
