import os
import shutil
import cv2
import logging
from datetime import datetime
from models.db import SessionLocal, Photo
from config.settings import PHOTO_DIR

logger = logging.getLogger(__name__)

"""
Модуль для работы с фотографиями задач (и тестовой задачи):
- сохранение кадра;
- очистка всех фото задачи;
- выборка путей к фото задачи (или тестовой задачи).
"""

def get_task_dir(task_id):
    if task_id == "test_task":
        return os.path.join(PHOTO_DIR, "test_task")
    return os.path.join(PHOTO_DIR, f"task_{task_id}")

def clear_photos_for_task(task_id):
    """
    Удаляет все фото задачи (и записи в БД для обычных задач).
    Для test_task — просто удаляет папку.
    """
    task_dir = get_task_dir(task_id)
    if task_id == "test_task":
        if os.path.isdir(task_dir):
            shutil.rmtree(task_dir)
        return

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
    if os.path.isdir(task_dir):
        try:
            os.rmdir(task_dir)
        except OSError:
            pass

def save_photo_for_task(task_id, frame, spectrum_id):
    """
    Сохраняет кадр (numpy/Opencv) для задачи или тестовой задачи.
    Для test_task — все фото с уникальным timestamp.
    Для обычных — по spectrum_id (одно фото на спектр, перезаписывает если нужно).
    """
    task_dir = get_task_dir(task_id)
    os.makedirs(task_dir, exist_ok=True)
    if task_id == "test_task":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"spectrum_{spectrum_id}_{timestamp}.jpg"
        path = os.path.join(task_dir, filename)
        cv2.imwrite(path, frame)
        return path

    filename = f"spectrum_{spectrum_id}.jpg"
    path = os.path.join(task_dir, filename)
    cv2.imwrite(path, frame)
    db = SessionLocal()
    photo = db.query(Photo).filter(Photo.task_id == task_id, Photo.spectrum_id == spectrum_id).first()
    if photo:
        photo.path = path
    else:
        photo = Photo(task_id=task_id, path=path, spectrum_id=spectrum_id)
        db.add(photo)
    db.commit()
    db.close()
    return path

def get_photos_for_task(task_id):
    """
    Возвращает список путей к фото задачи.
    Для test_task — просто все .jpg, отсортированные по времени создания.
    Для обычных — по spectrum_id из БД.
    """
    task_dir = get_task_dir(task_id)
    if not os.path.isdir(task_dir):
        return []
    if task_id == "test_task":
        photos = sorted(
            [os.path.join(task_dir, f) for f in os.listdir(task_dir) if f.endswith(".jpg")],
            key=lambda f: os.path.getmtime(f)
        )
        return photos

    db = SessionLocal()
    photos = db.query(Photo).filter(Photo.task_id == task_id).order_by(Photo.spectrum_id).all()
    db.close()
    return [photo.path for photo in photos]
