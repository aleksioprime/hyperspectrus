import requests
import json

def create_device_task(ip_address: str, title: str, spectra: list):
    """
    Отправляет HTTP-запрос на устройство для создания задачи
    """
    url = f"http://{ip_address}:8080/tasks"
    data = {
        "title": title,
        "spectra": spectra,
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=data, headers=headers, timeout=5)
    response.raise_for_status()
    return response.json()
