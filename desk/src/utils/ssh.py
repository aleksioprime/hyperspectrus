import paramiko

class SSHClient:
    def __init__(self, status_text):
        self.status_text = status_text
        self.client = None

    def connect(self, ip):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(ip, username="pi", password="raspberry")
            self.status_text.append("✅ Успешное подключение!")
        except Exception as e:
            self.status_text.append(f"❌ Ошибка подключения: {str(e)}")

    def upload_file(self, ip, file_path):
        if not self.client:
            self.connect(ip)

        try:
            sftp = self.client.open_sftp()
            sftp.put(file_path, "/home/pi/firmware.py")
            sftp.close()
            self.status_text.append(f"✅ Файл загружен на Raspberry")

            stdin, stdout, stderr = self.client.exec_command("sudo systemctl restart my_script.service")
            if stderr.read():
                self.status_text.append("⚠️ Ошибка при перезапуске")
            else:
                self.status_text.append("🔄 Сервис успешно перезапущен!")
        except Exception as e:
            self.status_text.append(f"❌ Ошибка загрузки: {str(e)}")
