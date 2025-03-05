import os
import socket
import struct
import pickle
import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from datetime import datetime


from PyQt5.QtCore import QThread, pyqtSignal
import socket

class VideoStreamWorker(QThread):
    update_status = pyqtSignal(str)  # Сигнал для обновления статуса
    connected_signal = pyqtSignal(bool)  # Сигнал успешного подключения

    def __init__(self, ip):
        super().__init__()
        self.ip = ip
        self.connected = False
        self.max_attempts = 3

    def run(self):
        """Фоновая попытка подключения к видеопотоку"""
        self.connection_attempts = 0

        while self.connection_attempts < self.max_attempts:
            self.connection_attempts += 1
            self.update_status.emit(f"Попытка подключения {self.connection_attempts}/{self.max_attempts}...")

            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(3)
                client_socket.connect((self.ip, 9999))

                self.update_status.emit("Ожидание первого кадра...")
                first_packet = client_socket.recv(4096)

                if not first_packet:
                    self.update_status.emit("Сервер не отправляет данные, соединение закрыто")
                    raise ConnectionError("Сервер не отправляет данные, соединение закрыто")

                self.connected = True
                self.update_status.emit("Подключено к видеопотоку")
                self.connected_signal.emit(True)  # Отправляем сигнал об успешном подключении
                return

            except Exception as e:
                self.update_status.emit(f"Ошибка подключения: {str(e)}")
                self.connected = False

        self.update_status.emit("Превышено число попыток подключения")
        self.connected_signal.emit(False)  # Подключение не удалось


class VideoStream:
    def __init__(self, video_label, status_text):
        self.video_label = video_label
        self.status_text = status_text
        self.connected = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.latest_frame = None
        self.client_socket = None

        self.placeholder_active = False
        self.connection_attempts = 0
        self.max_attempts = 3

        if not os.path.exists("records"):
            os.makedirs("records")

        self.placeholder_path = os.path.join("src/img", "no_signal.png")

    def create_placeholder(self):
        """Создаёт заглушку no_signal.png, если её нет"""
        img = 255 * np.ones((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "NO SIGNAL", (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imwrite(self.placeholder_path, img)

    def connect_to_video(self, ip):
        """Запуск фонового потока для подключения"""
        if self.connected:
            self.status_text.append("Уже подключено к видеопотоку")
            return

        self.connect_button.setEnabled(False)

        self.worker = VideoStreamWorker(ip)
        self.worker.update_status.connect(self.status_text.append)  # Обновление статуса
        self.worker.connected_signal.connect(self.on_connection_result)  # Проверка результата
        self.worker.start()  # Запуск фонового потока

    def on_connection_result(self, success):
        if success:
            self.connected = True
            self.timer.start(33)
        else:
            self.connect_button.setEnabled(True)

    def update_frame(self):
        """Получение и отображение кадров"""

        if not self.connected:
            if not self.placeholder_active:
                self.show_placeholder()
                self.placeholder_active = True
            return

        try:
            data = b""
            payload_size = struct.calcsize(">L")

            while len(data) < payload_size:
                packet = self.client_socket.recv(4096)
                if not packet:
                    self.status_text.append("Разрыв соединения")
                    self.connected = False
                    self.show_placeholder()
                    return
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            while len(data) < msg_size:
                data += self.client_socket.recv(4096)

            frame_data = data[:msg_size]
            self.latest_frame = pickle.loads(frame_data)
            frame = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)

            h, w, ch = frame.shape
            qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qimg))

            if not self.connected:
                self.connected = True
                self.status_text.append("Подключено к видеопотоку")

            self.placeholder_active = False

        except Exception as e:
            self.status_text.append(f"Ошибка получения видео: {e}")
            self.connected = False
            if not self.placeholder_active:
                self.show_placeholder()
                self.placeholder_active = True

    def show_placeholder(self):
        """Отображает картинку-заглушку при отсутствии видео"""
        if not os.path.exists(self.placeholder_path):
            self.create_placeholder()

        # Загружаем изображение заглушки
        placeholder = QPixmap(self.placeholder_path)

        if placeholder.isNull():
            self.status_text.append("Ошибка: не удалось загрузить заглушку!")
            return

        # Масштабируем изображение под размер QLabel
        self.video_label.setPixmap(placeholder.scaled(
            self.video_label.width(),
            self.video_label.height()
        ))

        self.status_text.append("Видео недоступно. Отображена заглушка")

    def enable_connect_button(self):
        """Разблокирует кнопку 'Подключиться' для повторных попыток"""
        self.status_text.append("🔄 Можно снова попытаться подключиться.")
        self.connect_button.setEnabled(True)  # Разблокируем кнопку

    def capture_frame(self):
        """Сохранение стоп-кадра."""
        if self.latest_frame is None:
            self.status_text.append("Видео недоступно, невозможно сохранить кадр")
            return

        # Генерация имени файла по дате
        filename = f"records/frame_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"

        try:
            cv2.imwrite(filename, self.latest_frame)
            self.status_text.append(f"Кадр сохранён: {filename}")
        except Exception as e:
            self.status_text.append(f"Ошибка сохранения кадра: {str(e)}")
