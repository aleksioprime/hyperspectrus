from PyQt5.QtWidgets import QFileDialog

from src.utils.ssh import SSHClient


class FirmwareUploader:
    def __init__(self, status_text):
        self.status_text = status_text
        self.selected_file = ""
        self.ssh_client = SSHClient(status_text)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Выберите прошивку", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.selected_file = file_path
            self.status_text.append(f"Выбран файл: {file_path}")

    def upload_file(self, ip):
        if not self.selected_file:
            self.status_text.append("Файл не выбран!")
            return
        self.ssh_client.upload_file(ip, self.selected_file)
