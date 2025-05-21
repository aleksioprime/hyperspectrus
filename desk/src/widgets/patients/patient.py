from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDateEdit, QTextEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import QDate

class PatientDialog(QDialog):
    """
    Диалоговое окно для создания или редактирования пациента
    """
    def __init__(self, parent=None, patient=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить пациента" if patient is None else "Редактировать пациента")
        self.patient = patient

        layout = QFormLayout(self)

        # --- Поля ввода данных ---
        self.name_edit = QLineEdit()
        self.birth_edit = QDateEdit()
        self.birth_edit.setDisplayFormat("dd.MM.yyyy")
        self.birth_edit.setCalendarPopup(True)
        self.notes_edit = QTextEdit()

        layout.addRow("ФИО пациента:", self.name_edit)
        layout.addRow("Дата рождения:", self.birth_edit)
        layout.addRow("Заметки:", self.notes_edit)

        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Если пациент передан — заполнить поля
        if patient:
            self.name_edit.setText(patient.full_name)
            if patient.birth_date:
                self.birth_edit.setDate(QDate(patient.birth_date.year, patient.birth_date.month, patient.birth_date.day))
            self.notes_edit.setText(patient.notes or "")

    def get_data(self):
        """
        Получить введённые данные пациента
        """
        bdate = self.birth_edit.date()
        return {
            "full_name": self.name_edit.text().strip(),
            "birth_date": bdate.toPyDate() if bdate.isValid() else None,
            "notes": self.notes_edit.toPlainText().strip()
        }
