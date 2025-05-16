from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QMessageBox
import api.cloud
import api.local

class PatientsWidget(QWidget):
    def __init__(self, on_patient_selected):
        super().__init__()
        self.on_patient_selected = on_patient_selected
        self.layout = QVBoxLayout(self)
        self.patients_list = QListWidget()
        self.layout.addWidget(QLabel("Список пациентов"))
        self.layout.addWidget(self.patients_list)
        self.patients = []
        self.patient_names = {}
        self.load_patients()
        self.patients_list.itemClicked.connect(self.select_patient)

    def load_patients(self):
        try:
            self.patients = api.cloud.get_patients()
            ids = [p["id"] for p in self.patients]
            self.patient_names = api.local.get_patient_names(ids)
            self.patients_list.clear()
            for p in self.patients:
                name = self.patient_names.get(str(p["id"]), "Неизвестно")
                self.patients_list.addItem(f"{p['id']}: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список пациентов:\n{e}")

    def select_patient(self, item):
        patient_id = int(item.text().split(":")[0])
        self.on_patient_selected(patient_id)
