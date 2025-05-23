from PyQt6.QtWidgets import QMainWindow

from ui.patient.patient_widget import PatientsWidget

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.setWindowTitle("HyperSpectRus v0.0.1")
        self.setFixedSize(950, 520)
        self.user = user
        self.is_logging_out = False  # Flag to indicate logout
        self.patients_widget = PatientsWidget(user) # Renaming for clarity as per instructions
        self.setCentralWidget(self.patients_widget)
        self.patients_widget.logout_requested.connect(self.handle_logout_request)

    def handle_logout_request(self):
        self.is_logging_out = True
        self.close()
