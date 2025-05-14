import os
import shutil
import cv2
from config.settings import PHOTO_DIR


def ensure_photo_dir():
    """Гарантирует, что директория для фото существует"""
    os.makedirs(PHOTO_DIR, exist_ok=True)


def clear_photos():
    """Удаляет все фотографии в директории и заново создаёт её."""
    if os.path.exists(PHOTO_DIR):
        shutil.rmtree(PHOTO_DIR)
    ensure_photo_dir()


def save_photo(frame, index):
    """Сохраняет кадр с камеры в файл с номером index."""
    ensure_photo_dir()
    path = os.path.join(PHOTO_DIR, f"photo_{index:02d}.jpg")
    cv2.imwrite(path, frame)


def get_photos():
    """Возвращает список путей к файлам фотографий."""
    ensure_photo_dir()
    return sorted([
        os.path.join(PHOTO_DIR, f) for f in os.listdir(PHOTO_DIR)
        if f.endswith(".jpg")
    ])
