import os
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QSizePolicy,
    QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from sqlalchemy.orm import joinedload
from skimage.filters import threshold_otsu
import uuid

from db.db import SessionLocal
from db.models import Session, RawImage, DeviceBinding, Chromophore, OverlapCoefficient, Result, ReconstructedImage


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
            photos_root = os.path.join(base_dir, "downloaded_photos")
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


class ProcessWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, object)  # bool: success, object: results_dict or error_message
    error = pyqtSignal(str) # For unexpected errors

    def __init__(self, session_id, parent=None):
        super().__init__(parent)
        self.session_id = session_id

    def run(self):
        """
        Performs image processing: calculation of chromophore concentrations, segmentation, and saving results.
        """
        db = None
        try:
            self.progress.emit("Начало обработки...")
            db = SessionLocal()

            # 1. Получаем все raw-фото для этой сессии, отсортированные по длине волны
            self.progress.emit("1/12: Загрузка сырых снимков из БД...")
            raw_images = (
                db.query(RawImage)
                .filter_by(session_id=self.session_id)
                .options(joinedload(RawImage.spectrum))
                .all()
            )
            if not raw_images:
                self.finished.emit(False, "Нет сырых снимков для обработки. Загрузите их с устройства.")
                return

            raw_images = sorted(raw_images, key=lambda x: x.spectrum.wavelength)
            n_spectra = len(raw_images)
            self.progress.emit(f"1/12: Найдено {n_spectra} сырых снимков.")

            # Проверяем размер всех картинок
            self.progress.emit("2/12: Проверка размеров изображений...")
            shapes = [Image.open(ri.file_path).size for ri in raw_images]
            if len(set(shapes)) != 1:
                self.finished.emit(False, "Все снимки должны быть одного размера!")
                return
            W, H = shapes[0]
            self.progress.emit(f"2/12: Размер изображений {W}x{H} OK.")

            # 2. Сборка гиперкуба (n_spectra, H, W)
            self.progress.emit("3/12: Сборка гиперкуба...")
            cube = np.stack(
                [np.array(Image.open(ri.file_path).convert("L"), dtype=np.float32) for ri in raw_images],
                axis=0
            )
            self.progress.emit("3/12: Гиперкуб собран.")

            # 3. Получаем коэффициенты перекрытия (матрицу) для всех спектров и хромофоров
            self.progress.emit("4/12: Загрузка коэффициентов перекрытия...")
            chromophores = db.query(Chromophore).order_by(Chromophore.id).all()
            n_chroms = len(chromophores)
            if n_chroms == 0:
                self.finished.emit(False, "В базе данных отсутствуют хромофоры.")
                return
            
            overlap_matrix = np.zeros((n_spectra, n_chroms), dtype=np.float32)
            for i, ri in enumerate(raw_images):
                for j, chrom in enumerate(chromophores):
                    coef = (
                        db.query(OverlapCoefficient)
                        .filter_by(spectrum_id=ri.spectrum_id, chromophore_id=chrom.id)
                        .first()
                    )
                    if coef is None:
                        # self.finished.emit(False, f"Отсутствует коэффициент перекрытия для спектра {ri.spectrum.wavelength}nm и хромофора {chrom.symbol}.")
                        # return # This might be too strict, allow processing with zero if missing
                        overlap_matrix[i, j] = 0.0 
                        self.progress.emit(f"Предупреждение: Коэффициент для {ri.spectrum.wavelength}nm / {chrom.symbol} не найден, используется 0.0")
                    else:
                        overlap_matrix[i, j] = coef.coefficient
            self.progress.emit("4/12: Коэффициенты перекрытия загружены.")

            # 4. Ищем референс-снимки (пропущено, как и в оригинале)
            self.progress.emit("5/12: Поиск референсных снимков (пропущено)...")
            # ref_cube = None; ref_found = False

            # 5. Преобразуем к оптической плотности (OD)
            self.progress.emit("6/12: Расчет оптической плотности (OD)...")
            cube_norm = np.clip(cube / 255.0, 1e-6, 1.0) # Add epsilon to avoid log(0)
            OD = -np.log10(cube_norm)
            self.progress.emit("6/12: OD рассчитана.")

            # 6. Вычисляем концентрации всех хромофоров
            self.progress.emit("7/12: Расчет карт концентраций хромофоров...")
            concentration_maps = np.zeros((n_chroms, H, W), dtype=np.float32)
            for y in range(H):
                for x in range(W):
                    y_vec = OD[:, y, x]
                    try:
                        x_vec, residuals, rank, s = np.linalg.lstsq(overlap_matrix, y_vec, rcond=None)
                        concentration_maps[:, y, x] = x_vec
                    except np.linalg.LinAlgError as lae:
                        # self.progress.emit(f"Ошибка линейной алгебры при расчете пикселя ({x},{y}): {lae}") # Too verbose
                        concentration_maps[:, y, x] = 0 # Fallback for problematic pixels
            self.progress.emit("7/12: Карты концентраций рассчитаны.")

            # 7. Суммируем Hb + HbO2
            self.progress.emit("8/12: Расчет общей концентрации гемоглобина (THb)...")
            idx_hbo2 = next((i for i, c in enumerate(chromophores) if c.symbol.lower() in ["hbo2", "hb02"]), None)
            idx_hb = next((i for i, c in enumerate(chromophores) if c.symbol.lower() == "hb"), None)

            if idx_hbo2 is not None and idx_hb is not None:
                thb_map = np.abs(concentration_maps[idx_hbo2]) + np.abs(concentration_maps[idx_hb])
            elif idx_hbo2 is not None: # Only HbO2 found
                thb_map = np.abs(concentration_maps[idx_hbo2])
                self.progress.emit("Предупреждение: Хромофор Hb не найден, THb = |HbO2|.")
            elif idx_hb is not None: # Only Hb found
                thb_map = np.abs(concentration_maps[idx_hb])
                self.progress.emit("Предупреждение: Хромофор HbO2 не найден, THb = |Hb|.")
            elif n_chroms > 0 : # Fallback if specific Hb symbols are not found
                thb_map = np.abs(concentration_maps[0])
                self.progress.emit(f"Предупреждение: Hb и HbO2 не найдены. THb основан на первом хромофоре: {chromophores[0].symbol}.")
            else: # Should have been caught by n_chroms == 0 earlier
                 self.finished.emit(False, "Нет хромофоров для расчета THb.")
                 return
            self.progress.emit("8/12: THb рассчитан.")

            # 8. Сегментация по Otsu
            self.progress.emit("9/12: Сегментация изображения (Otsu)...")
            thb_norm = (thb_map - np.nanmin(thb_map)) / (np.nanmax(thb_map) - np.nanmin(thb_map) + 1e-8)
            thb_img_uint8 = (thb_norm * 255).astype(np.uint8)
            try:
                threshold_value = threshold_otsu(thb_img_uint8)
            except Exception as otsu_e: # Catch potential errors if image is flat
                self.progress.emit(f"Ошибка Otsu: {otsu_e}. Используется порог 128.")
                threshold_value = 128 
            mask_lesion = thb_img_uint8 >= threshold_value
            mask_skin = thb_img_uint8 < threshold_value
            self.progress.emit("9/12: Сегментация завершена.")

            # 9. Статистики
            self.progress.emit("10/12: Расчет статистик...")
            mean_lesion_thb = float(np.nanmean(thb_map[mask_lesion])) if np.any(mask_lesion) else 0.0
            mean_skin_thb = float(np.nanmean(thb_map[mask_skin])) if np.any(mask_skin) else 0.0
            s_coefficient = mean_lesion_thb / mean_skin_thb if mean_skin_thb > 1e-6 else 0.0 # Avoid division by zero
            self.progress.emit("10/12: Статистики рассчитаны.")

            # 10. Сохраняем изображения (THb и сегментация)
            self.progress.emit("11/12: Сохранение карт изображений...")
            # Ensure base directory from a raw image exists
            base_photo_dir = os.path.dirname(raw_images[0].file_path)
            processed_dir = os.path.join(base_photo_dir, f"processed_{self.session_id}")
            os.makedirs(processed_dir, exist_ok=True)

            thb_img_path = os.path.join(processed_dir, "thb_map.png")
            Image.fromarray((thb_norm * 255).astype(np.uint8)).save(thb_img_path)
            mask_img_path = os.path.join(processed_dir, "mask_otsu.png")
            Image.fromarray((mask_lesion * 255).astype(np.uint8)).save(mask_img_path)

            # 11. Удаляем старые записи из базы и сохраняем ReconstructedImage для каждого хромофора
            self.progress.emit("12/12: Обновление БД и сохранение реконструированных изображений...")
            old_reconstructed_imgs = db.query(ReconstructedImage).filter_by(session_id=self.session_id).all()
            for old_img in old_reconstructed_imgs:
                try:
                    if os.path.isfile(old_img.file_path):
                        os.remove(old_img.file_path)
                except Exception as e_remove:
                    self.progress.emit(f"Не удалось удалить старый файл {old_img.file_path}: {e_remove}")
                db.delete(old_img)
            db.flush()

            for i, chrom in enumerate(chromophores):
                img_path = os.path.join(processed_dir, f"{chrom.symbol.replace('/', '_')}.png") # Sanitize filename
                # Normalize individual chromophore map
                chrom_map_data = concentration_maps[i]
                min_val = np.nanmin(chrom_map_data)
                max_val = np.nanmax(chrom_map_data)
                range_val = max_val - min_val + 1e-8 # Add epsilon for flat images
                
                img_norm = (chrom_map_data - min_val) / range_val
                Image.fromarray((img_norm * 255).astype(np.uint8)).save(img_path)
                
                rec_img = ReconstructedImage(
                    id=str(uuid.uuid4()),
                    session_id=self.session_id,
                    chromophore_id=chrom.id,
                    file_path=img_path,
                )
                db.add(rec_img)

            # 12. Сохраняем результат (Result)
            old_result = db.query(Result).filter_by(session_id=self.session_id).first()
            if old_result:
                db.delete(old_result)
                db.flush()

            result_obj = Result(
                id=str(uuid.uuid4()),
                session_id=self.session_id,
                contour_path=mask_img_path,
                thb_path=thb_img_path,
                s_coefficient=s_coefficient,
                mean_lesion_thb=mean_lesion_thb,
                mean_skin_thb=mean_skin_thb,
                notes="Автоматическая обработка (поточная)"
            )
            db.add(result_obj)
            db.commit()
            self.progress.emit("12/12: Результаты сохранены в БД.")

            results_data = {
                "s_coefficient": s_coefficient,
                "mean_lesion_thb": mean_lesion_thb,
                "mean_skin_thb": mean_skin_thb,
                "thb_map_path": thb_img_path,
                "mask_path": mask_img_path,
                "chromophore_images": {chrom.symbol: os.path.join(processed_dir, f"{chrom.symbol.replace('/', '_')}.png") for chrom in chromophores}
            }
            self.finished.emit(True, results_data)

        except Exception as e:
            if db:
                db.rollback()
            detailed_error_msg = f"Ошибка в ProcessWorker: {type(e).__name__} - {e}"
            import traceback
            detailed_error_msg += f"\nTraceback: {traceback.format_exc()}"
            self.error.emit(detailed_error_msg) # For unexpected errors
            self.finished.emit(False, f"Ошибка обработки: {e}") # General message for UI
        finally:
            if db:
                db.close()


class SessionWidget(QWidget):
    """
    Окно просмотра и управления результатами сеанса.
    Показывает сведения о пациенте и сеансе, статус задачи, загрузку и просмотр фото (raw и processed).
    """

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Информация о сеансе")
        self.session = session
        self.device_api_url = f"http://{self.session.device_binding.ip_address}:8080"
        self.task_id = self.session.device_task_id

        # --- ВЕРХНИЙ БЛОК ---
        upper_layout = QHBoxLayout()

        # 1. Информация о пациенте/сеансе

        info_layout = QVBoxLayout()
        label_patient = QLabel(f"ФИО пациента: {self.session.patient.full_name}")
        label_patient.setWordWrap(True)
        info_layout.addWidget(label_patient)
        info_layout.addWidget(QLabel(f"Дата рождения: {self.session.patient.birth_date.strftime('%d.%m.%Y')}"))
        info_layout.addWidget(QLabel(f"Дата сеанса: {self.session.date.strftime('%d.%m.%Y %H:%M')}"))
        info_layout.addWidget(QLabel(f"Оператор: {self.session.operator.full_name if self.session.operator else ''}"))
        info_layout.addWidget(QLabel(f"Заметки: {self.session.notes or ''}"))

        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        upper_layout.addWidget(info_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # 2. Статус устройства, IP, кнопки
        device_layout = QVBoxLayout()
        label_device = QLabel(f"Устройство: {self.session.device_binding.device.name if self.session.device_binding else ''}")
        label_device.setWordWrap(True)
        device_layout.addWidget(label_device)
        ip_addr = self.session.device_binding.ip_address if self.session.device_binding else ""
        device_layout.addWidget(QLabel(f"IP: {ip_addr}"))
        self.status_label = QLabel("Статус: -")
        device_layout.addWidget(self.status_label)

        self.refresh_status_btn = QPushButton("Обновить статус")
        self.download_photos_btn = QPushButton("Загрузить фото с устройства")
        device_layout.addWidget(self.refresh_status_btn)
        device_layout.addWidget(self.download_photos_btn)

        device_widget = QWidget()
        device_widget.setLayout(device_layout)
        upper_layout.addWidget(device_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # 3. Общий анализ (заглушка, но будет динамически обновляться)
        analysis_layout = QVBoxLayout()
        self.analys_label = QLabel("Общий анализ: -")
        analysis_layout.addWidget(self.analys_label)
        self.s_coefficient = QLabel("S-коэффициент: -")
        analysis_layout.addWidget(self.s_coefficient)
        self.lesion_thb = QLabel("Thb (очаг): -")
        analysis_layout.addWidget(self.lesion_thb)
        self.skin_thb = QLabel("Thb (кожа): -")
        analysis_layout.addWidget(self.skin_thb)
        analysis_widget = QWidget()
        analysis_widget.setLayout(analysis_layout)
        upper_layout.addWidget(analysis_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # --- НИЖНИЙ БЛОК ---
        lower_layout = QHBoxLayout()

        # 1. Сырые фото: таблица и предпросмотр
        raw_side = QVBoxLayout()
        raw_side.addWidget(QLabel("Сырые снимки:"))

        raw_table_block = QHBoxLayout()
        self.raw_table = QTableWidget(0, 1)
        self.raw_table.setFixedWidth(100)
        self.raw_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.raw_table.setHorizontalHeaderLabels(["Спектр"])
        self.raw_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.raw_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.raw_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.raw_table.itemSelectionChanged.connect(self.on_raw_photo_selected)
        raw_table_block.addWidget(self.raw_table)

        self.raw_view = QLabel("Нет фото")
        self.raw_view.setMinimumSize(180, 135)
        self.raw_view.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.raw_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        raw_table_block.addWidget(self.raw_view)

        raw_side.addLayout(raw_table_block)
        lower_layout.addLayout(raw_side)

        # 2. Обработанные фото: таблица и предпросмотр (можно позже реализовать)
        proc_side = QVBoxLayout()
        proc_side.addWidget(QLabel("Обработанные снимки:"))

        proc_table_block = QHBoxLayout()
        self.proc_table = QTableWidget(0, 1)
        self.proc_table.setFixedWidth(100)
        self.proc_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.proc_table.setHorizontalHeaderLabels(["Хромофор"])
        self.proc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.proc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.proc_table.itemSelectionChanged.connect(self.on_proc_photo_selected)
        proc_table_block.addWidget(self.proc_table)

        self.proc_view = QLabel("Нет фото")
        self.proc_view.setMinimumSize(180, 135)
        self.proc_view.setAlignment(Qt.AlignmentFlag.AlignTop)
        proc_table_block.addWidget(self.proc_view)

        proc_side.addLayout(proc_table_block)
        lower_layout.addLayout(proc_side)

        bottom_button = QHBoxLayout()
        # --- Кнопка обработки ---
        self.process_btn = QPushButton("Обработка")
        self.process_btn.setFixedWidth(120)
        self.process_btn.setEnabled(False)
        bottom_button.addWidget(self.process_btn)

        self.back_btn = QPushButton("Назад")
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.close)
        bottom_button.addStretch()
        bottom_button.addWidget(self.back_btn)

        # --- Основной layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(upper_layout)
        main_layout.addSpacing(3)
        main_layout.addLayout(lower_layout)
        main_layout.addLayout(bottom_button)

        # --- Сигналы ---
        self.refresh_status_btn.clicked.connect(self.update_task_status)
        self.download_photos_btn.clicked.connect(self.start_photo_download)
        self.process_btn.clicked.connect(self.process_results)

        # --- Инициализация данных ---
        self.thread = None
        self.download_worker = None
        self.processing_thread = None # Added for ProcessWorker
        self.process_worker = None    # Added for ProcessWorker
        self.update_task_status()
        self.load_raw_photos()
        self.load_proc_photos()
        self.update_analysis_block()

    def _add_row(self, layout, row, label_text, value_text):
        label = QLabel(label_text)
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        value = QLabel(value_text)
        value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label, row, 0)
        layout.addWidget(value, row, 1)

    def refresh_session_data(self):
        session_db = SessionLocal()
        self.session = session_db.query(Session).options(
            joinedload(Session.patient),
            joinedload(Session.device_binding).joinedload(DeviceBinding.device),
            joinedload(Session.operator),
            joinedload(Session.result),
            ).get(self.session.id)
        session_db.close()
        self.update_analysis_block()

    def update_analysis_block(self):
        """
        Обновляет текст анализа по self.session.result.
        """
        result = self.session.result
        if result:
            self.analys_label.setText("Общий анализ: выполнен")
            self.s_coefficient.setText(f"S-коэффициент: {result.s_coefficient:.3f}")
            self.lesion_thb.setText(f"Thb (очаг): {result.mean_lesion_thb:.3f}")
            self.skin_thb.setText(f"Thb (кожа): {result.mean_skin_thb:.3f}")
        else:
            self.analys_label.setText("Общий анализ: не выполнен")

    def update_task_status(self):
        """
        Обновляет статус задачи на устройстве (по кнопке).
        Если задача не найдена — блокирует загрузку фото и обработку.
        """
        if self.task_id is None:
            self.status_label.setText("Статус: задача не найдена")
            self.download_photos_btn.setEnabled(False)
            return

        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/status"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 404:
                self.status_label.setText("Статус: задача не найдена")
                self.download_photos_btn.setEnabled(False)
                return
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "Статус: —")
            self.status_label.setText(status)
            # Включаем обработку только если фото уже есть локально и статус "completed"
            if status == "completed" and self.has_photos():
                self.process_btn.setEnabled(True)
            else:
                self.process_btn.setEnabled(False)
            self.download_photos_btn.setEnabled(True)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                self.status_label.setText("Статус: задача не найдена")
                self.download_photos_btn.setEnabled(False)
                self.process_btn.setEnabled(False)
            else:
                self.status_label.setText("Статус: ошибка обновления")
                print(f"Ошибка при обновлении статуса: {e}")
                self.process_btn.setEnabled(False)
                self.download_photos_btn.setEnabled(False)
        except Exception as e:
            self.status_label.setText("Статус: ошибка обновления")
            print(f"Ошибка при обновлении статуса: {e}")
            self.process_btn.setEnabled(False)
            self.download_photos_btn.setEnabled(False)

    def load_raw_photos(self):
        """
        Загружает и отображает сырые фото (RawImage), связанные с этим сеансом.
        В таблице: №, спектр (wavelength).
        """
        session = SessionLocal()
        photos = (
            session.query(RawImage)
            .filter_by(session_id=self.session.id)
            .options(joinedload(RawImage.spectrum))
            .all()
        )
        session.close()
        self.raw_table.setRowCount(0)
        self._raw_paths = []  # сохраняем пути для предпросмотра
        for i, photo in enumerate(photos):
            self.raw_table.insertRow(i)
            spec_str = str(photo.spectrum.wavelength) if photo.spectrum and getattr(photo.spectrum, "wavelength", None) is not None else "?"
            self.raw_table.setItem(i, 0, QTableWidgetItem(spec_str))
            self._raw_paths.append(photo.file_path)
        # Заглушка в окне предпросмотра
        if self.raw_table.rowCount() == 0:
            self.raw_view.setText("Нет фото")
        else:
            self.raw_view.setText("Выберите фото слева")

        self.process_btn.setEnabled(self.has_photos())

    def load_proc_photos(self):
        """
        Загружает и отображает обработанные снимки (ReconstructedImage), связанные с этим сеансом.
        В таблице: №, хромофор (symbol).
        """
        session = SessionLocal()
        images = (
            session.query(ReconstructedImage)
            .filter_by(session_id=self.session.id)
            .options(joinedload(ReconstructedImage.chromophore))
            .all()
        )
        session.close()
        self.proc_table.setRowCount(0)
        self._proc_paths = []
        for i, img in enumerate(images):
            self.proc_table.insertRow(i)
            chrom_str = img.chromophore.symbol if img.chromophore else "?"
            self.proc_table.setItem(i, 0, QTableWidgetItem(chrom_str))
            self._proc_paths.append(img.file_path)
        if self.proc_table.rowCount() == 0:
            self.proc_view.setText("Нет фото")
        else:
            self.proc_view.setText("Выберите фото слева")


    def on_raw_photo_selected(self):
        """
        Показывает выбранное raw фото в предпросмотре.
        """
        selected = self.raw_table.selectedItems()
        if not selected:
            self.raw_view.setText("Выберите фото слева")
            return
        idx = selected[0].row()
        if idx < 0 or idx >= len(self._raw_paths):
            self.raw_view.setText("Файл не найден")
            return
        path = self._raw_paths[idx]
        if not os.path.isfile(path):
            self.raw_view.setText("Файл не найден")
            return
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.raw_view.setPixmap(pixmap.scaled(
                self.raw_view.width(), self.raw_view.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.raw_view.setText("Ошибка загрузки фото")

    def on_proc_photo_selected(self):
        """
        Показывает выбранное обработанное фото в предпросмотре.
        """
        selected = self.proc_table.selectedItems()
        if not selected:
            self.proc_view.setText("Выберите фото слева")
            return
        idx = selected[0].row()
        if idx < 0 or idx >= len(self._proc_paths):
            self.proc_view.setText("Файл не найден")
            return
        path = self._proc_paths[idx]
        if not os.path.isfile(path):
            self.proc_view.setText("Файл не найден")
            return
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.proc_view.setPixmap(pixmap.scaled(
                self.proc_view.width(), self.proc_view.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.proc_view.setText("Ошибка загрузки фото")


    def has_photos(self) -> bool:
        """
        Проверяет, есть ли в таблице загруженные фото.
        """
        return self.raw_table.rowCount() > 0

    def start_photo_download(self):
        if self.task_id is None:
            QMessageBox.warning(self, "Ошибка", "ID задачи не найден. Обновите статус.")
            return

        if self.thread is not None and self.thread.isRunning():
            QMessageBox.information(self, "Загрузка", "Загрузка уже выполняется.")
            return

        self.thread = QThread(self)
        self.download_worker = DownloadWorker(self.session.id, self.device_api_url)
        self.download_worker.task_id = self.task_id
        self.download_worker.moveToThread(self.thread)

        # Connect signals and slots
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)

        self.thread.started.connect(self.download_worker.run)
        # Clean up worker and thread
        self.download_worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        # Also ensure cleanup on error
        self.download_worker.error.connect(self.thread.quit) # Ensure thread quits on error
        # self.thread.finished.connect(self.download_worker.deleteLater) # Already connected via finished

        self.download_photos_btn.setEnabled(False)
        self.status_label.setText("Статус: Загрузка фото...")
        self.thread.start()

    def on_download_progress(self, message: str):
        self.status_label.setText(f"Статус: {message}")

    def on_download_finished(self, saved_count: int, message: str):
        QMessageBox.information(self, "Загрузка завершена", f"{message}\nСохранено фото: {saved_count}")
        self.load_raw_photos() # Refresh the list of raw photos
        self.process_btn.setEnabled(self.has_photos())
        self.download_photos_btn.setEnabled(True)
        self.status_label.setText(f"Статус: Загрузка завершена. {message}")
        # Reset thread and worker references
        self.thread = None
        self.download_worker = None


    def on_download_error(self, message: str):
        QMessageBox.warning(self, "Ошибка загрузки", message)
        self.download_photos_btn.setEnabled(True)
        self.status_label.setText(f"Статус: Ошибка загрузки. {message}")
        # Reset thread and worker references
        if self.thread and self.thread.isRunning(): # Ensure thread is quit if error signal is emitted before finished
            self.thread.quit()
            self.thread.wait() # Wait for thread to finish before deleting
        self.thread = None
        self.download_worker = None

    def on_processing_thread_finished(self):
        """Slot to clean up processing thread and worker."""
        if self.processing_thread: # Check if it hasn't been set to None already
            self.processing_thread.deleteLater()
        if self.process_worker: # Check if it hasn't been set to None already
            self.process_worker.deleteLater()
        self.processing_thread = None
        self.process_worker = None
        # Re-enable buttons after thread is confirmed finished
        self.process_btn.setEnabled(self.has_photos()) # Enable only if photos are present
        self.download_photos_btn.setEnabled(True)


    def process_results(self):
        """
        Initiates image processing in a separate thread using ProcessWorker.
        """
        if self.processing_thread is not None and self.processing_thread.isRunning():
            QMessageBox.information(self, "Обработка", "Процесс обработки уже запущен.")
            return

        if not self.has_photos():
            QMessageBox.warning(self, "Нет фото", "Сначала загрузите снимки с устройства!")
            return

        self.processing_thread = QThread(self)
        self.process_worker = ProcessWorker(session_id=self.session.id)
        self.process_worker.moveToThread(self.processing_thread)

        # Connect signals for progress, completion, and errors
        self.process_worker.progress.connect(self.on_processing_progress)
        self.process_worker.finished.connect(self.on_processing_finished)
        self.process_worker.error.connect(self.on_processing_error) # For unhandled exceptions in worker

        # Connect thread lifecycle signals
        self.processing_thread.started.connect(self.process_worker.run)
        # When worker signals it's done (finished or error), tell the thread to quit
        self.process_worker.finished.connect(self.processing_thread.quit)
        self.process_worker.error.connect(self.processing_thread.quit)
        
        # When the thread actually finishes, schedule cleanup
        self.processing_thread.finished.connect(self.on_processing_thread_finished)


        # Update UI: disable buttons, show status
        self.process_btn.setEnabled(False)
        self.download_photos_btn.setEnabled(False) # Disable photo downloads during processing
        self.status_label.setText("Статус: Обработка изображений...")
        
        self.processing_thread.start()

    def on_processing_progress(self, message: str):
        """Handles progress updates from ProcessWorker."""
        self.status_label.setText(f"Статус: Обработка... {message}")

    def on_processing_finished(self, success: bool, results_or_error: object):
        """Handles the finished signal from ProcessWorker."""
        if success:
            results_dict = results_or_error
            s_coefficient = results_dict.get("s_coefficient", 0.0)
            mean_lesion_thb = results_dict.get("mean_lesion_thb", 0.0)
            mean_skin_thb = results_dict.get("mean_skin_thb", 0.0)

            # Update UI labels for analysis results
            self.analys_label.setText("Общий анализ: выполнен (поточная)") # Indicate it's from threaded processing
            self.s_coefficient.setText(f"S-коэффициент: {s_coefficient:.3f}")
            self.lesion_thb.setText(f"Thb (очаг): {mean_lesion_thb:.3f}")
            self.skin_thb.setText(f"Thb (кожа): {mean_skin_thb:.3f}")
            
            self.load_proc_photos() # Refresh the table of processed images
            self.refresh_session_data() # Refresh session data which might update other UI parts

            QMessageBox.information(
                self, 
                "Обработка завершена",
                f"Готово!\nS-коэффициент: {s_coefficient:.2f}\nTHb (очаг): {mean_lesion_thb:.2f}\nTHb (кожа): {mean_skin_thb:.2f}"
            )
            self.status_label.setText("Статус: Обработка успешно завершена.")
        else:
            error_message = str(results_or_error)
            QMessageBox.warning(self, "Ошибка обработки", error_message)
            self.status_label.setText(f"Статус: Ошибка обработки. {error_message}")

        # Buttons are re-enabled in on_processing_thread_finished to ensure thread is fully done.
        # However, process_btn logic might need adjustment based on state (e.g. if it can be retried)
        # For now, it's handled by on_processing_thread_finished.

    def on_processing_error(self, message: str):
        """Handles unexpected errors from ProcessWorker."""
        QMessageBox.critical(self, "Критическая ошибка обработки", f"Произошла непредвиденная ошибка: {message}")
        self.status_label.setText(f"Статус: Критическая ошибка обработки! {message}")
        # Buttons re-enabled by on_processing_thread_finished after thread quits.

    def closeEvent(self, event):
        # Ensure download thread is cleaned up if widget is closed
        if self.thread is not None and self.thread.isRunning():
            self.status_label.setText("Статус: Завершение загрузки фото...")
            self.thread.quit()
            self.thread.wait(3000) # Wait up to 3 seconds
        
        # Ensure processing thread is cleaned up if widget is closed
        if self.processing_thread is not None and self.processing_thread.isRunning():
            self.status_label.setText("Статус: Завершение обработки...")
            self.processing_thread.quit()
            self.processing_thread.wait(5000) # Wait up to 5 seconds

        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # Центрируем окно
        screen = self.screen().availableGeometry()
        size = self.frameGeometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

