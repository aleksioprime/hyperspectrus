import pytest
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton

from src.ui.user.user_profile_dialog import UserProfileDialog
from src.db.models import User

def test_user_profile_dialog_displays_user_info_no_name(qtbot):
    """Test display with a user having username, email, but no first/last name."""
    mock_user = User(
        username="testuser_no_name",
        email="test_no_name@example.com",
        is_superuser=True
        # first_name and last_name are None by default
    )

    dialog = UserProfileDialog(user=mock_user)
    qtbot.addWidget(dialog)

    assert dialog.username_input.text() == "testuser_no_name"
    assert dialog.username_input.isReadOnly()

    assert dialog.first_name_input.text() == "N/A" # Default for None
    assert dialog.first_name_input.isReadOnly()

    assert dialog.last_name_input.text() == "N/A" # Default for None
    assert dialog.last_name_input.isReadOnly()

    assert dialog.email_input.text() == "test_no_name@example.com"
    assert dialog.email_input.isReadOnly()

    assert dialog.is_superuser_input.text() == "Да" # is_superuser=True
    assert dialog.is_superuser_input.isReadOnly()

def test_user_profile_dialog_displays_user_info_full(qtbot):
    """Test display with a user having all information including first/last name."""
    mock_user_full = User(
        username="fulluser",
        first_name="Full",
        last_name="User",
        email="full@example.com",
        is_superuser=False
    )

    dialog = UserProfileDialog(user=mock_user_full)
    qtbot.addWidget(dialog)

    assert dialog.username_input.text() == "fulluser"
    assert dialog.username_input.isReadOnly()

    assert dialog.first_name_input.text() == "Full"
    assert dialog.first_name_input.isReadOnly()

    assert dialog.last_name_input.text() == "User"
    assert dialog.last_name_input.isReadOnly()

    assert dialog.email_input.text() == "full@example.com"
    assert dialog.email_input.isReadOnly()

    assert dialog.is_superuser_input.text() == "Нет" # is_superuser=False
    assert dialog.is_superuser_input.isReadOnly()

def test_user_profile_dialog_displays_user_info_with_org_field_absent(qtbot):
    """
    Test display with a user associated with an organization.
    The current UserProfileDialog does not display organization info,
    so this test effectively checks that it doesn't break and shows other info correctly.
    """
    # Mocking an organization object with a 'name' attribute
    mock_org = type('MockOrg', (), {'name': 'TestCorp'})()

    mock_user_with_org = User(
        username="orguser",
        first_name="Org",
        last_name="User",
        email="org@example.com",
        is_superuser=False,
        organization=mock_org # Assigning the mock organization
    )

    dialog = UserProfileDialog(user=mock_user_with_org)
    qtbot.addWidget(dialog)

    # Check standard fields are still displayed correctly
    assert dialog.username_input.text() == "orguser"
    assert dialog.first_name_input.text() == "Org"
    assert dialog.last_name_input.text() == "User"
    assert dialog.email_input.text() == "org@example.com"
    assert dialog.is_superuser_input.text() == "Нет"

    # Verify no QLineEdit was accidentally created for organization
    # (assuming all QLineEdits are direct children of the dialog or its main layout's form_layout)
    # This is a bit fragile, depends on layout structure.
    # A better check might be ensuring number of QFormLayout rows if it were fixed.
    found_org_field = False
    for child in dialog.findChildren(QLineEdit):
        if "TestCorp" in child.text(): # Simple check
            found_org_field = True
            break
    assert not found_org_field, "Organization field should not be displayed by current dialog"


def test_user_profile_dialog_ok_button(qtbot):
    """Test that clicking the OK button accepts the dialog."""
    mock_user = User(
        username="okuser",
        email="ok@example.com"
    )

    dialog = UserProfileDialog(user=mock_user)
    qtbot.addWidget(dialog)

    # The OK button is self.ok_button
    assert dialog.ok_button is not None
    assert dialog.ok_button.text() == "OK"

    # Simulate a click on the OK button
    # qtbot.mouseClick(dialog.ok_button, Qt.MouseButton.LeftButton)
    # Or, since it's connected to self.accept:
    dialog.ok_button.click()

    assert dialog.result() == QDialog.DialogCode.Accepted
