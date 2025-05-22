import os
import requests

from PyQt6.QtCore import pyqtSignal, QObject

from db.db import SessionLocal
from db.models import RawImage


class DownloadWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(int, str)
    error = pyqtSignal(str)

    def __init__(self, session_id, device_api_url, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.device_api_url = device_api_url
        self.task_id = None # This will be set before running, if needed, or passed to run()

    def run(self):
        """
        Downloads photos from the device, saves them, and updates the database.
        This method is intended to be run in a separate thread.
        """
        if self.task_id is None: # task_id should be set before calling run
            self.error.emit("ID задачи не найден")
            self.finished.emit(0, "Ошибка: ID задачи не был предоставлен.")
            return

        try:
            self.progress.emit("Запрос списка фотографий...")
            url = f"{self.device_api_url}/tasks/{self.task_id}/photos"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            photos_data = resp.json()

            if not photos_data:
                self.progress.emit("Нет фотографий для загрузки.")
                self.finished.emit(0, "Нет новых фотографий для загрузки.")
                return

            saved_count = 0
            total_photos = len(photos_data)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            photos_root = os.path.join(base_dir, "photos")
            session_dir = os.path.join(photos_root, f"session_{self.session_id}")
            os.makedirs(session_dir, exist_ok=True)

            session_db = SessionLocal()
            try:
                for i, photo_info in enumerate(photos_data):
                    spectrum_id = photo_info.get("spectrum_id")
                    self.progress.emit(f"Загрузка фото {i+1}/{total_photos} (Spectrum ID: {spectrum_id})...")

                    exists = session_db.query(RawImage).filter_by(session_id=self.session_id, spectrum_id=spectrum_id).first()
                    if exists:
                        self.progress.emit(f"Фото {i+1}/{total_photos} (Spectrum ID: {spectrum_id}) уже существует. Пропуск.")
                        continue

                    download_url_suffix = photo_info.get("download_url")
                    if not download_url_suffix:
                        self.progress.emit(f"Отсутствует URL для загрузки фото {i+1}/{total_photos}. Пропуск.")
                        continue

                    download_url = f"{self.device_api_url}/{download_url_suffix.lstrip('/')}"

                    img_resp = requests.get(download_url, timeout=20)
                    if img_resp.status_code == 200:
                        fname = os.path.join(session_dir, f"spectrum_{spectrum_id}.jpg")
                        with open(fname, "wb") as f:
                            f.write(img_resp.content)

                        raw_image = RawImage(
                            session_id=self.session_id,
                            file_path=fname,
                            spectrum_id=spectrum_id
                        )
                        session_db.add(raw_image)
                        saved_count += 1
                    else:
                        error_msg = f"Не удалось скачать фото с spectrum_id={spectrum_id}. Статус: {img_resp.status_code}"
                        self.progress.emit(error_msg)
                        # Decide if this is a critical error or if we should continue
                        # For now, let's continue but report it later via finished or a specific error signal.

                session_db.commit()
                self.finished.emit(saved_count, f"Загружено новых фото: {saved_count}")
            except Exception as db_e:
                session_db.rollback()
                self.error.emit(f"Ошибка базы данных: {db_e}")
                self.finished.emit(saved_count, f"Ошибка базы данных при сохранении. Загружено: {saved_count}")
            finally:
                session_db.close()

        except requests.exceptions.RequestException as req_e:
            self.error.emit(f"Ошибка сети: {req_e}")
            self.finished.emit(0, f"Ошибка сети: {req_e}")
        except Exception as e:
            self.error.emit(f"Непредвиденная ошибка: {e}")
            self.finished.emit(0, f"Непредвиденная ошибка: {e}")