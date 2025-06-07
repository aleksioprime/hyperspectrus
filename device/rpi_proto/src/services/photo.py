from models.db import SessionLocal, PhotoTask, Photo
import os
import cv2

from config.settings import PHOTO_DIR

"""
Работа с фотографиями: сохранение, удаление, выборка для задачи.
"""

def clear_photos_for_task(task_id):
    """
    Удаляет все фото, связанные с задачей, из файловой системы и базы.
    """
    db = SessionLocal()
    photos = db.query(Photo).filter(Photo.task_id == task_id).all()
    for photo in photos:
        try:
            os.remove(photo.path)
        except FileNotFoundError:
            pass
        db.delete(photo)
    db.commit()
    db.close()
    # Также удаляем папку задачи, если она пуста
    task_dir = os.path.join(PHOTO_DIR, f"task_{task_id}")
    if os.path.isdir(task_dir):
        try:
            os.rmdir(task_dir)
        except OSError:
            pass  # Папка не пуста — оставляем

def save_photo_for_task(task_id, frame, spectrum_id):
    """
    Сохраняет кадр OpenCV для задачи с заданным spectrum_id.
    Фото сохраняются в подпапку для задачи.
    """
    # Создаём папку для задачи, если её нет
    task_dir = os.path.join(PHOTO_DIR, f"task_{task_id}")
    os.makedirs(task_dir, exist_ok=True)
    filename = f"spectrum_{spectrum_id}.jpg"
    path = os.path.join(task_dir, filename)
    cv2.imwrite(path, frame)
    db = SessionLocal()
    # Проверим, нет ли уже фото с таким спектром (на случай пересъёмки)
    photo = db.query(Photo).filter(Photo.task_id == task_id, Photo.spectrum_id == spectrum_id).first()
    if photo:
        # Перезаписываем файл и обновляем дату
        photo.path = path
    else:
        photo = Photo(task_id=task_id, path=path, spectrum_id=spectrum_id)
        db.add(photo)
    db.commit()
    db.close()

def get_photos_for_task(task_id):
    """
    Возвращает список путей к фотографиям задачи по порядку spectrum_id.
    """
    db = SessionLocal()
    photos = db.query(Photo).filter(Photo.task_id == task_id).order_by(Photo.spectrum_id).all()
    db.close()
    return [photo.path for photo in photos]
