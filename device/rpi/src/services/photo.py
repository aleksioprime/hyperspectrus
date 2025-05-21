from models.db import SessionLocal, PhotoTask, Photo
import os
import cv2
import datetime

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

def save_photo_for_task(task_id, frame, index):
    """
    Сохраняет кадр OpenCV для задачи с индексом.
    """
    filename = f"task{task_id}_photo_{index:02d}.jpg"
    path = os.path.join(PHOTO_DIR, filename)
    cv2.imwrite(path, frame)
    db = SessionLocal()
    photo = Photo(task_id=task_id, path=path, index=index)
    db.add(photo)
    db.commit()
    db.close()

def get_photos_for_task(task_id):
    """
    Возвращает список путей к фотографиям задачи по порядку.
    """
    db = SessionLocal()
    photos = db.query(Photo).filter(Photo.task_id == task_id).order_by(Photo.index).all()
    db.close()
    return [photo.path for photo in photos]
