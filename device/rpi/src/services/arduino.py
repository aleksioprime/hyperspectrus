
import time
import serial
import glob
from PyQt5.QtCore import QThread, pyqtSignal


class ArduinoController:
    def __init__(self, baudrate=9600, timeout=1, wait=True):
        self.ser = None
        self.port = None

        port = self.find_port()
        if port:
            try:
                self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
                self.port = port
                if wait:
                    time.sleep(2)  # Arduino ресетится при подключении — подождать
            except serial.SerialException as e:
                print(f"Ошибка подключения к Arduino: {e}")
        else:
            print("❌ Порт Arduino не найден")

    def find_port(self):
        # Поиск среди доступных устройств
        candidates = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        for path in candidates:
            try:
                # Проверка возможности открытия
                with serial.Serial(path, timeout=1) as test:
                    return path
            except serial.SerialException:
                continue
        return None

    def send_and_wait(self, command: str, expected_response: str, timeout: float = 3.0) -> bool:
        if not self.ser or not self.ser.is_open:
            print("⚠️ Порт закрыт или не инициализирован")
            return False

        try:
            self.ser.reset_input_buffer()
            self.ser.write((command + '\n').encode())
        except serial.SerialException as e:
            print(f"⚠️ Не удалось отправить команду {command!r}: {e}")
            return False

        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode(errors='ignore').strip()
                    print(f"← Arduino: {line}")
                    if line == expected_response:
                        return True
            except serial.SerialException as e:
                print(f"⚠️ Ошибка чтения из порта: {e}")
                return False
            time.sleep(0.05)

        print(f"⚠️ Таймаут: не получен {expected_response!r} на {command!r}")
        return False

    def close(self):
        if self.ser:
            self.ser.close()


class ArduinoWatcher(QThread):
    status_changed = pyqtSignal(bool, str)  # найден?, порт

    def __init__(self, check_interval=2):
        super().__init__()
        self._running = True
        self._last_status = None
        self.check_interval = check_interval

    def run(self):
        while self._running:
            ctrl = ArduinoController(wait=False)
            available = ctrl.ser is not None
            port = ctrl.port if ctrl.ser else ""
            ctrl.close()

            if available != self._last_status:
                self._last_status = available
                self.status_changed.emit(available, port)

            time.sleep(self.check_interval)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()