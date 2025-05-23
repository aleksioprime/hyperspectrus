from PyQt6.QtWidgets import QMainWindow

from ui.patient.patient_widget import PatientsWidget

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.setWindowTitle("HyperSpectRus v0.0.1")
        self.setFixedSize(950, 520)
        self.user = user
        self.patients = PatientsWidget(user)
        self.setCentralWidget(self.patients)
