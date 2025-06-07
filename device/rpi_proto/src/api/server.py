import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models.db import SessionLocal, PhotoTask, Photo, init_db

app = FastAPI()

# ----------------------- Pydantic схемы ----------------------------

class SpectrumIn(BaseModel):
    # Схема для одного спектра при создании задачи (id справочника и параметры RGB)
    id: str
    rgb: List[int]

class PhotoTaskIn(BaseModel):
    # Схема запроса создания задачи: название + список спектров (каждый - id + rgb)
    title: str
    spectra: List[SpectrumIn]

class SpectrumOut(SpectrumIn):
    # Схема для вывода спектра в API-ответах (совпадает с входной)
    pass

class PhotoTaskOut(BaseModel):
    # Схема для вывода задачи (id, название, список спектров, статус)
    id: str
    title: str
    spectra: List[SpectrumOut]
    status: str

# ----------------------- API эндпойнты ----------------------------

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    """
    Корневой эндпойнт для проверки работоспособности сервиса (ping).
    """
    return {"status": "ok"}

@app.get("/tasks", response_model=List[PhotoTaskOut])
def list_tasks():
    """
    Получить список всех задач.
    Возвращает все задачи с их спектрами и статусами.
    """
    db = SessionLocal()
    try:
        tasks = db.query(PhotoTask).all()
        # Поскольку spectra хранится как JSON-список dict'ов, отдаём его как есть
        result = [
            PhotoTaskOut(id=task.id, title=task.title, spectra=task.spectra, status=task.status)
            for task in tasks
        ]
        return result
    finally:
        db.close()

@app.post("/tasks", response_model=PhotoTaskOut)
def create_task(task: PhotoTaskIn):
    """
    Создать новую задачу (серия спектров).
    - title: строка (название задачи)
    - spectra: список объектов {"id": ..., "rgb": [...]}
    """
    db = SessionLocal()
    try:
        # Преобразуем spectra в список dict'ов для записи как JSON в БД
        obj = PhotoTask(title=task.title, spectra=[s.dict() for s in task.spectra])
        db.add(obj)
        db.commit()
        db.refresh(obj)
        # Возвращаем полную инфу о задаче (id, title, spectra, status)
        return PhotoTaskOut(
            id=obj.id, title=obj.title, spectra=obj.spectra, status=obj.status
        )
    finally:
        db.close()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    """
    Удалить задачу и все связанные с ней фото.
    """
    db = SessionLocal()
    try:
        task = db.query(PhotoTask).get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        # Если есть каскад в модели, можно удалить только task
        db.query(Photo).filter(Photo.task_id == task_id).delete()
        db.delete(task)
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@app.get("/tasks/{task_id}/photos")
def get_photos(task_id: str):
    """
    Получить список фото по задаче.
    Возвращает список словарей:
    - spectrum_id: id спектра из справочника
    - download_url: относительный путь для скачивания через API
    """
    db = SessionLocal()
    try:
        photos = db.query(Photo).filter(Photo.task_id == task_id).order_by(Photo.spectrum_id).all()
        result = []
        for p in photos:
            result.append({
                "spectrum_id": p.spectrum_id,
                "download_url": f"/tasks/{task_id}/photos/{p.spectrum_id}/download"
            })
        return result
    finally:
        db.close()

@app.get("/tasks/{task_id}/status")
def get_task_status(task_id: str):
    """
    Получить статус задачи по её ID.
    Статус может быть, например: "pending", "completed"
    """
    db = SessionLocal()
    try:
        task = db.query(PhotoTask).get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return {"id": task.id, "title": task.title, "status": task.status}
    finally:
        db.close()

@app.get("/tasks/{task_id}/photos/{spectrum_id}/download")
def download_photo(task_id: str, spectrum_id: str):
    """
    Скачать фото по идентификатору спектра (spectrum_id), если задача завершена.
    - Проверяет, что задача существует и завершена.
    - Находит фото с этим спектром.
    - Если файл существует — возвращает его с корректным именем и типом.
    """
    db = SessionLocal()
    try:
        task = db.query(PhotoTask).get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        if task.status != "completed":
            raise HTTPException(status_code=400, detail="Задача ещё не завершена")
        # Ищем фото с нужным spectrum_id
        photo = db.query(Photo).filter(Photo.task_id == task_id, Photo.spectrum_id == spectrum_id).first()
        if not photo or not os.path.exists(photo.path):
            raise HTTPException(status_code=404, detail="Фото не найдено")
        fname = os.path.basename(photo.path)
        return FileResponse(photo.path, filename=fname, media_type="image/jpeg")
    finally:
        db.close()

# -------------------- ВАЖНО --------------------
# - Во всех ответах используется spectrum_id для идентификации фото.
# - На клиенте для скачивания фото используйте download_url.
# - В Photo должны быть поля: task_id, spectrum_id (id справочника спектров), path (путь к файлу).
# - В PhotoTask.spectra хранится список объектов с id и rgb, чтобы знать параметры и порядок спектров для задачи.
# - Все доступы к БД обёрнуты в try/finally для гарантированного закрытия сессии.
