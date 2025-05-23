import sys
from PyQt6.QtWidgets import QApplication, QDialog

from ui.main_window import MainWindow
from ui.login_widget import LoginDialog
from ui.create_user_widget import CreateUserDialog
from db.db import init_db, has_users # Removed get_db_session, User as they are no longer directly used here
# from db.models import User # No longer directly used here

def center_window_on_screen(window):
    screen = window.screen().availableGeometry()
    size = window.frameGeometry()
    x = (screen.width() - size.width()) // 2
    y = (screen.height() - size.height()) // 2
    window.move(x, y)

def main():
    init_db()
    app = QApplication(sys.argv)

    # Use the new has_users() function
    proceed_to_login = False

    if not has_users():
        # No users exist, show create user dialog
        create_user_dialog = CreateUserDialog()
        if create_user_dialog.exec() == QDialog.DialogCode.Accepted:
            proceed_to_login = True
        else:
            # User cancelled creation, exit
            sys.exit(0)
    else:
        # Users exist
        proceed_to_login = True

    if proceed_to_login:
        login_dialog = LoginDialog()
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            user = login_dialog.user
            main_window = MainWindow(user)
            main_window.show()
            center_window_on_screen(main_window)
            sys.exit(app.exec())
        else:
            # User cancelled login, exit
            sys.exit(0)
    else:
        # This case should ideally not be reached if logic is correct,
        # but as a fallback, exit.
        sys.exit(0)

if __name__ == "__main__":
    main()
