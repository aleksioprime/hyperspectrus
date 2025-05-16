from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QLineEdit, QMessageBox
import api.local

class QueueWidget(QWidget):
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self.layout = QVBoxLayout(self)
        self.spectra_input = QLineEdit(); self.spectra_input.setPlaceholderText('["RED","GREEN"]')
        add_job_btn = QPushButton("Создать задание для Raspberry")
        self.jobs_list = QListWidget()
        self.layout.addWidget(QLabel(f"Очередь заданий для сессии {session_id}"))
        self.layout.addWidget(self.spectra_input)
        self.layout.addWidget(add_job_btn)
        self.layout.addWidget(self.jobs_list)
        add_job_btn.clicked.connect(self.add_job)
        self.load_jobs()

    def add_job(self):
        spectra = eval(self.spectra_input.text())  # В реальном коде использовать json.loads!
        try:
            api.local.add_job_to_queue(self.session_id, spectra)
            self.spectra_input.clear()
            self.load_jobs()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать задание:\n{e}")

    def load_jobs(self):
        try:
            jobs = api.local.get_jobs()
            self.jobs_list.clear()
            for job in jobs:
                self.jobs_list.addItem(f"#{job['id']}: сессия {job['session_id']}, статус: {job['status']}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить очередь заданий:\n{e}")
