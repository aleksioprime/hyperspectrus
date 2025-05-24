import pytest

def test_pytest_is_working():
    assert True

# If pytest-qt is intended to be checked, a simple Qt test:
def test_qt_import(qtbot): # qtbot fixture indicates pytest-qt is active
    from PyQt6.QtWidgets import QPushButton
    button = QPushButton("Test")
    assert button.text() == "Test"
