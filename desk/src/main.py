import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox
from auth.login import LoginDialog
from widgets.patient import PatientsWidget
from widgets.session import SessionsWidget
from widgets.queue import QueueWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Клиника — рабочее место")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.patients_tab = QWidget(); self.sessions_tab = QWidget(); self.queue_tab = QWidget()
        self.tabs.addTab(self.patients_tab, "Пациенты")
        self.tabs.addTab(self.sessions_tab, "Сессии")
        self.tabs.addTab(self.queue_tab, "Очередь")
        self.init_patients_tab()
        self.current_patient_id = None
        self.current_session_id = None

    def init_patients_tab(self):
        layout = QVBoxLayout(self.patients_tab)
        self.patients_widget = PatientsWidget(self.on_patient_selected)
        layout.addWidget(self.patients_widget)

    def on_patient_selected(self, patient_id):
        self.current_patient_id = patient_id
        # Инициализация вкладки сессий
        self.sessions_tab.setLayout(QVBoxLayout())
        self.sessions_widget = SessionsWidget(patient_id, self.on_session_selected)
        self.sessions_tab.layout().addWidget(self.sessions_widget)
        self.tabs.setCurrentWidget(self.sessions_tab)

    def on_session_selected(self, session_id):
        self.current_session_id = session_id
        self.queue_tab.setLayout(QVBoxLayout())
        self.queue_widget = QueueWidget(session_id)
        self.queue_tab.layout().addWidget(self.queue_widget)
        self.tabs.setCurrentWidget(self.queue_tab)

def main():
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec() != login.Accepted:
        sys.exit()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
