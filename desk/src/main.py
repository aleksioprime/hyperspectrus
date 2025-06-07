import sys
from PyQt6.QtWidgets import QApplication, QDialog

from ui.main_window import MainWindow
from ui.login_widget import LoginDialog
from ui.user.create_user_widget import CreateUserDialog
from db.db import init_db, has_users

import logging.config
from core.logging import LOGGING

logging.config.dictConfig(LOGGING)


def center_window_on_screen(window):
    """
    Центрирует переданное окно относительно экрана пользователя
    """
    screen = window.screen().availableGeometry()
    size = window.frameGeometry()
    x = (screen.width() - size.width()) // 2
    y = (screen.height() - size.height()) // 2
    window.move(x, y)

def main():
    """
    Точка входа в приложение.
    Инициализация БД, запуск QApplication, логика авторизации и выхода/выхода из учётки.
    """
    init_db()
    app = QApplication(sys.argv)

    while True:
        # Если в базе нет пользователей (первый запуск):
        if not has_users():
            # Открываем диалог создания первого пользователя
            create_user_dialog = CreateUserDialog()
            if create_user_dialog.exec() != QDialog.DialogCode.Accepted:
                # Если диалог закрыли без создания пользователя — приложение завершает работу
                sys.exit(0)

        # Открываем окно авторизации
        login = LoginDialog()
        if login.exec() == QDialog.DialogCode.Accepted:
            user = login.user
            # Запускаем основное окно приложения (и передаём туда пользователя)
            win = MainWindow(user)
            win.show()

            center_window_on_screen(win)

            # Запускаем основной Qt event loop (ждём, пока пользователь не закроет окно)
            app_exit_code = app.exec()

            # Проверяем, был ли инициирован выход из аккаунта (например, нажали "Выйти" внутри MainWindow)
            if hasattr(win, 'is_logging_out') and win.is_logging_out:
                # Если пользователь выбрал выход из аккаунта — очищаем окно, повторяем цикл (вернёмся к авторизации)
                del win
                continue
            else:
                # Если был обычный выход (закрытие окна) — завершаем приложение и передаём exit code системе
                sys.exit(app_exit_code)
        else:
            # Если диалог авторизации был отменён — выходим из приложения
            sys.exit(0)

if __name__ == "__main__":
    # Точка входа при запуске main.py
    main()
