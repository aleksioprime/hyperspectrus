import os
import numpy as np
from PIL import Image
from sqlalchemy.orm import joinedload
from skimage.filters import threshold_otsu
import uuid

from PyQt6.QtCore import pyqtSignal, QObject

from db.db import SessionLocal
from db.models import RawImage, Chromophore, OverlapCoefficient, Result, ReconstructedImage


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
