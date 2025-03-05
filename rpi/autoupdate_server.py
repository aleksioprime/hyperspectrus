import socket
import os
import subprocess

HOST = "0.0.0.0"  # Слушаем все интерфейсы
PORT = 5000       # Порт для связи

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Сервер обновления запущен на {HOST}:{PORT}")

while True:
    conn, addr = server_socket.accept()
    print(f"Подключение от {addr}")

    # Получаем имя файла
    filename = conn.recv(1024).decode()
    filepath = f"/home/pi/{filename}"

    # Получаем сам файл
    with open(filepath, "wb") as f:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            f.write(data)

    print(f"Файл {filename} загружен.")

    # Перезапускаем сервис (если он есть)
    try:
        subprocess.run(["sudo", "systemctl", "restart", "my_script.service"], check=True)
        print("Сервис my_script.service перезапущен!")
    except subprocess.CalledProcessError:
        print("Ошибка при перезапуске!")

    conn.close()