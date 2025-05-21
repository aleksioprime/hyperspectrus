from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt


class ConfirmDialog(QDialog):
    """
    Кастомный диалог подтверждения без кнопки [X] и сворачивания.
    """

    def __init__(self, parent, title: str, text: str, yes_text="Да", no_text="Нет"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)  # Без [X] и сворачивания

        layout = QVBoxLayout()
        layout.addWidget(QLabel(text))

        btn_yes = QPushButton(yes_text)
        btn_no = QPushButton(no_text)

        btn_yes.clicked.connect(lambda: self.done(1))
        btn_no.clicked.connect(lambda: self.done(0))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    @staticmethod
    def confirm(parent, title: str, text: str, yes_text="Да", no_text="Нет") -> bool:
        """
        Статический метод: показывает диалог и возвращает True/False.
        """
        dlg = ConfirmDialog(parent, title, text, yes_text, no_text)
        return dlg.exec_() == 1
