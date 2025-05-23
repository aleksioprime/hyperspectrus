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

    while True:
        if not has_users():
            create_user_dialog = CreateUserDialog()
            if create_user_dialog.exec() != QDialog.DialogCode.Accepted:
                sys.exit(0)
        
        login = LoginDialog()
        if login.exec() == QDialog.DialogCode.Accepted:
            user = login.user
            win = MainWindow(user)
            win.show()
            center_window_on_screen(win)
            
            app_exit_code = app.exec()

            if hasattr(win, 'is_logging_out') and win.is_logging_out:
                del win
                continue  # Re-enter the loop to show login dialog
            else:
                sys.exit(app_exit_code) # Normal window close
        else:
            # Login dialog was cancelled
            sys.exit(0)

if __name__ == "__main__":
    main()
