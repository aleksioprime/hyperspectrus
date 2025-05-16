from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QPushButton, QHBoxLayout, QLineEdit, QMessageBox
import api.cloud

class SessionsWidget(QWidget):
    def __init__(self, patient_id, on_session_selected):
        super().__init__()
        self.patient_id = patient_id
        self.on_session_selected = on_session_selected
        self.layout = QVBoxLayout(self)
        self.sessions_list = QListWidget()
        self.layout.addWidget(QLabel(f"Сессии пациента {patient_id}"))
        self.layout.addWidget(self.sessions_list)
        self.session_desc_input = QLineEdit(); self.session_desc_input.setPlaceholderText("Описание сессии")
        add_btn = QPushButton("Создать сессию")
        del_btn = QPushButton("Удалить сессию")
        h = QHBoxLayout()
        h.addWidget(self.session_desc_input)
        h.addWidget(add_btn)
        h.addWidget(del_btn)
        self.layout.addLayout(h)
        self.sessions = []
        self.load_sessions()
        self.sessions_list.itemClicked.connect(self.select_session)
        add_btn.clicked.connect(self.add_session)
        del_btn.clicked.connect(self.del_session)

    def load_sessions(self):
        try:
            self.sessions = api.cloud.get_sessions(self.patient_id)
            self.sessions_list.clear()
            for s in self.sessions:
                self.sessions_list.addItem(f"{s['id']}: {s['description']}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сессии:\n{e}")

    def select_session(self, item):
        session_id = int(item.text().split(":")[0])
        self.on_session_selected(session_id)

    def add_session(self):
        desc = self.session_desc_input.text()
        try:
            api.cloud.create_session(self.patient_id, desc)
            self.session_desc_input.clear()
            self.load_sessions()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать сессию:\n{e}")

    def del_session(self):
        item = self.sessions_list.currentItem()
        if not item:
            return
        session_id = int(item.text().split(":")[0])
        try:
            api.cloud.delete_session(session_id)
            self.load_sessions()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сессию:\n{e}")
