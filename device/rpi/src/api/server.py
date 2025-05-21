import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models.db import SessionLocal, PhotoTask, Photo, init_db

"""
FastAPI-сервер: REST-API для управления задачами и просмотром фото.
"""

app = FastAPI()

class PhotoTaskIn(BaseModel):
    title: str
    spectra: List[List[int]]

class PhotoTaskOut(BaseModel):
    id: int
    title: str
    spectra: List[List[int]]
    status: str

@app.get("/tasks", response_model=List[PhotoTaskOut])
def list_tasks():
    """
    Получить список всех задач.
    """
    db = SessionLocal()
    tasks = db.query(PhotoTask).all()
    result = [
        PhotoTaskOut(id=task.id, title=task.title, spectra=task.spectra, status=task.status)
        for task in tasks
    ]
    db.close()
    return result

@app.post("/tasks", response_model=PhotoTaskOut)
def create_task(task: PhotoTaskIn):
    """
    Создать новую задачу (серия спектров).
    """
    db = SessionLocal()
    obj = PhotoTask(title=task.title, spectra=task.spectra)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    db.close()
    return PhotoTaskOut(id=obj.id, title=obj.title, spectra=obj.spectra, status=obj.status)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """
    Удалить задачу и все связанные с ней фото.
    """
    db = SessionLocal()
    task = db.query(PhotoTask).get(task_id)
    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()
    db.close()
    return {"ok": True}

@app.get("/tasks/{task_id}/photos")
def get_photos(task_id: int):
    """
    Получить список фото по задаче.
    """
    db = SessionLocal()
    photos = db.query(Photo).filter(Photo.task_id == task_id).order_by(Photo.index).all()
    db.close()
    return [{"index": p.index, "path": p.path} for p in photos]

@app.get("/tasks/{task_id}/status")
def get_task_status(task_id: int):
    """
    Получить статус задачи по её ID (например: pending, completed).
    """
    db = SessionLocal()
    task = db.query(PhotoTask).get(task_id)
    db.close()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"id": task.id, "title": task.title, "status": task.status}

@app.get("/tasks/{task_id}/photos/{index}/download")
def download_photo(task_id: int, index: int):
    """
    Скачать фото для задачи, если задача завершена.
    """
    db = SessionLocal()
    task = db.query(PhotoTask).get(task_id)
    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.status != "completed":
        db.close()
        raise HTTPException(status_code=400, detail="Задача ещё не завершена")
    photo = db.query(Photo).filter(Photo.task_id == task_id, Photo.index == index).first()
    db.close()
    if not photo or not os.path.exists(photo.path):
        raise HTTPException(status_code=404, detail="Фото не найдено")
    # Для браузеров подставим корректное имя файла
    fname = os.path.basename(photo.path)
    return FileResponse(photo.path, filename=fname, media_type="image/jpeg")
