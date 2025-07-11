import logging
import time

import numpy as np
import imageio.v2 as imageio
import cv2
import os
import scipy.linalg as spla

from src.core.config import settings
from src.models.patient import Session, RawImage, ReconstructedImage, Result
from src.models.parameter import Spectrum, Chromophore, OverlapCoefficient
from src.db.postgres import SyncSessionLocal
from src.constants.celery import CeleryStatus
from src.celery_app import celery_app

logger = logging.getLogger(__name__)


def cleanup_session_results_if_no_raw_images(session_id, db):
    raw_images_count = db.query(RawImage).filter(RawImage.session_id == session_id).count()
    if raw_images_count == 0:
        # Удаляем reconstructed images и их файлы
        logger.info(f"Удаление восстановленных изображений и их файлов")
        rec_images = db.query(ReconstructedImage).filter(ReconstructedImage.session_id == session_id).all()
        for rec in rec_images:
            rel_path = rec.file_path.removeprefix(settings.media.reconstructed_images_url).lstrip("/")
            abs_path = os.path.join(settings.media.reconstructed_images_path, rel_path)
            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                except Exception as e:
                    logger.warning(f"Ошибка при удалении файла {abs_path}: {e}")

        db.query(ReconstructedImage).filter(ReconstructedImage.session_id == session_id).delete(synchronize_session=False)
        db.commit()

    # Удаляем результат и файл контура
    logger.info(f"Удаление результата и файла контура")
    result = db.query(Result).filter(Result.session_id == session_id).first()
    if result:
        if result.contour_path:
            rel_path = result.contour_path.removeprefix(settings.media.contour_url).lstrip("/")
            abs_path = os.path.join(settings.media.contour_path, rel_path)
            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                except Exception as e:
                    logger.warning(f"Ошибка при удалении файла {abs_path}: {e}")
        db.query(Result).filter(Result.session_id == session_id).delete(synchronize_session=False)
        db.commit()

    logger.info(f"Удалены производные результаты и reconstructed images для сеанса {session_id} (raw_images отсутствуют)")



def analyze_hyperspectral_session(db, session):
    """
    Выполняет обработку гиперспектральных снимков для заданного сеанса.
    Возвращает словарь с вычисленными метриками и путями к результатам.
    """
    # 1. Собираем raw images для сеанса, сортируем по спектрам
    raw_images = db.query(RawImage).filter(RawImage.session_id == session.id).all()
    if not raw_images:
        logger.warning(f"Нет исходных изображений для сеанса {session.id}. Очищаю производные данные…")
        return None

    logger.info(f"Исходные изображения (кол-во: {len(raw_images)}): {[img.file_path for img in raw_images]}")

    # Собираем спектры и хромофоры устройства
    spectra = db.query(Spectrum).filter(Spectrum.device_id == session.device.id).order_by(Spectrum.wavelength).all()
    chromophores = db.query(Chromophore).order_by(Chromophore.id).all()

    logger.info(f"Спектры устройства (кол-во: {len(spectra)}): {[s.wavelength for s in spectra]}")
    logger.info(f"Хромофоры (кол-во: {len(chromophores)}): {[c.symbol for c in chromophores]}")

    # Строим матрицу перекрытий
    overlap_matrix = np.zeros((len(spectra), len(chromophores)), dtype=float)
    for i, spectrum in enumerate(spectra):
        for j, chrom in enumerate(chromophores):
            coeff = db.query(OverlapCoefficient)\
                .filter_by(spectrum_id=spectrum.id, chromophore_id=chrom.id)\
                .first()
            overlap_matrix[i, j] = coeff.coefficient if coeff else 0.0

    logger.info(f"Матрица перекрытий: shape={overlap_matrix.shape}, пример={overlap_matrix[:2,:2].tolist()}")

    # Нормирование матрицы перекрытий
    max_value = np.abs(overlap_matrix).max()
    if max_value > 0:
        overlap_matrix = overlap_matrix / max_value
    logger.info(f"Матрица перекрытий нормирована: max={overlap_matrix.max()}, min={overlap_matrix.min()}")

    # 2. Читаем изображения, приводим к одному размеру и диапазону [0, 255]
    img_map = {img.spectrum_id: img for img in raw_images}
    images = []
    missing_spectra = []

    for spectrum in spectra:
        img_obj = img_map.get(spectrum.id)
        if img_obj is None:
            missing_spectra.append(spectrum.wavelength)
            continue

        file_path = os.path.join(
            settings.media.raw_images_path,
            img_obj.file_path.removeprefix(settings.media.raw_images_url).lstrip("/")
        )
        if not os.path.exists(file_path):
            logger.error(f"Файл изображения не найден: {file_path}")
            missing_spectra.append(spectrum.wavelength)
            continue

        img = imageio.imread(file_path)
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img = img.astype(np.float32)  # Явно float32 для дальнейших расчётов

        images.append(img)

    if missing_spectra:
        logger.error(f"Нет изображений для спектров: {missing_spectra}")
        return None

    # Проверка размеров — все изображения должны быть одинаковые
    shapes = [im.shape for im in images]
    if len(set(shapes)) != 1:
        logger.error(f"Изображения имеют разные размеры: {shapes}")
        return None

    images = np.stack(images, axis=0)
    logger.info(f"Считано {images.shape[0]} изображений, итоговый shape: {images.shape}")

    # 3. Преобразуем к OD через деление на 255 (чтобы OD был в ожидаемом диапазоне)
    cube_norm = np.clip(images / 255.0, 1e-6, 1.0)  # На случай переполнения и деления на 0
    logger.info(f"Диапазон изображений после нормализации: min={cube_norm.min()}, max={cube_norm.max()}")
    OD = -np.log10(cube_norm)

    logger.info(f"OD гист: {[np.min(OD), np.max(OD), np.mean(OD), np.std(OD)]}")

    # 4. Решаем систему для концентраций по каждому пикселю через least squares
    _, H, W = images.shape
    concentrations = np.zeros((len(chromophores), H, W), dtype=np.float32)
    for y in range(H):
        for x in range(W):
            od_col = OD[:, y, x]
            try:
                x_vec, *_ = np.linalg.lstsq(overlap_matrix, od_col, rcond=None)
                concentrations[:, y, x] = x_vec
            except Exception as e:
                logger.debug(f"Ошибка решения СЛАУ в точке ({y}, {x}): {e}")
                concentrations[:, y, x] = 0.0
    logger.info(f"Полученная концентрация: shape={concentrations.shape}, min={concentrations.min()}, max={concentrations.max()}")
    logger.info(f"Сondition number overlap_matrix: {np.linalg.cond(overlap_matrix)}")
    for i, chrom in enumerate(chromophores):
        img = concentrations[i]
        logger.info(f"{chrom.symbol}: min={img.min()}, max={img.max()}, mean={img.mean()}, std={img.std()}")

    # 5. Строим итоговую карту THb (сумма по гемоглобинам)
    idx_hbo2 = next((i for i, c in enumerate(chromophores) if c.symbol.strip().lower() in ('hbo2',)), None)
    idx_hb   = next((i for i, c in enumerate(chromophores) if c.symbol.strip().lower() == 'hb'), None)
    if idx_hbo2 is None or idx_hb is None:
        logger.error(f"В базе не найден HbO2 или Hb! symbols: {[c.symbol for c in chromophores]}")
        return None

    thb_map = np.abs(concentrations[idx_hbo2]) + np.abs(concentrations[idx_hb])
    logger.info(f"THb карта построена, shape: {thb_map.shape}")
    logger.info(f"THb гист: {[np.min(thb_map), np.max(thb_map), np.mean(thb_map), np.std(thb_map)]}")

    # 6. Сегментация OTSU
    if np.isnan(thb_map).any():
        logger.warning("В THb карте есть NaN!")
        thb_map = np.nan_to_num(thb_map, nan=0.0, posinf=0.0, neginf=0.0)

    ptp = np.ptp(thb_map)
    if ptp == 0 or np.isnan(ptp):
        thb_norm = np.zeros_like(thb_map, dtype=np.uint8)
    else:
        thb_norm = ((thb_map - thb_map.min()) / ptp * 255).astype(np.uint8)

    logger.info(f"THb min: {thb_map.min()}, max: {thb_map.max()}, ptp: {ptp}")

    alpha = 0.5
    threshold = np.min(thb_norm) + alpha * (np.max(thb_norm) - np.min(thb_norm))
    blur = cv2.GaussianBlur(thb_norm, (5, 5), 2)
    _, mask = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY_INV)
    mask_ratio = np.count_nonzero(mask) / mask.size
    logger.info(f"Threshold={threshold:.1f} (alpha={alpha}), mask ratio={mask_ratio:.4f}")


    # 7. Статистика по зонам
    lesion = thb_map[mask > 0]
    skin = thb_map[mask == 0]
    mean_lesion = float(np.mean(lesion)) if lesion.size else 0.0
    mean_skin = float(np.mean(skin)) if skin.size else 1e-6
    s_coeff = mean_lesion / mean_skin if mean_skin else 0.0
    logger.info(f"Статистика: mean_lesion={mean_lesion}, mean_skin={mean_skin}, s_coeff={s_coeff}")

    # 8. Сохраняем контурное изображение
    os.makedirs(settings.media.contour_path, exist_ok=True)

    color_thb = cv2.normalize(thb_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    color_thb = cv2.cvtColor(color_thb, cv2.COLOR_GRAY2BGR)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(color_thb, contours, -1, (0, 0, 255), 2)
    filename = f"contour_{session.id}.png"
    contour_path = os.path.join(settings.media.contour_path, filename)
    contour_url = os.path.join(settings.media.contour_url, filename)
    cv2.imwrite(contour_path, color_thb)
    logger.info(f"Контурное изображение сохранено: {contour_path} (url: {contour_url})")

    # 9. Сохраняем reconstructed карты по каждому хромофору
    os.makedirs(settings.media.reconstructed_images_path, exist_ok=True)

    reconstructed_images = []
    for i, chrom in enumerate(chromophores):
        img = concentrations[i]

        filename = f"rec_{chrom.symbol}_{session.id}.png"
        rec_path = os.path.join(settings.media.reconstructed_images_path, filename)
        rec_url = os.path.join(settings.media.reconstructed_images_url, filename)

        img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        success = cv2.imwrite(rec_path, img_norm)
        if not success:
            logger.error(f"Ошибка сохранения reconstructed карты: {rec_path}")

        reconstructed_images.append({
            'chromophore_id': str(chrom.id),
            'file_path': rec_url
        })
    logger.info(f"Сохранено карт реконструкции: {len(reconstructed_images)} в каталоге: {settings.media.reconstructed_images_path}")

    def fmt(x):
        if abs(x) > 0 and (abs(x) < 0.001 or abs(x) > 1000):
            return f"{x:.3e}"
        return round(x, 3)

    return {
        'contour_path': contour_url,
        's_coefficient': fmt(s_coeff),
        'mean_lesion_thb': fmt(mean_lesion),
        'mean_skin_thb': fmt(mean_skin),
        'reconstructed_images': reconstructed_images
    }


def update_session_fields(session_id, **fields):
    with SyncSessionLocal() as db:
        obj = db.query(Session).filter(Session.id == session_id).first()
        if obj:
            for key, value in fields.items():
                setattr(obj, key, value)
            db.commit()
            logger.info(f"Обновлены поля {fields} в сеансе {session_id}")
        else:
            logger.warning(f"Сеанс {session_id} не найден для обновления {fields}")


@celery_app.task(bind=True)
def process_session(self, session_id: str):
    update_session_fields(session_id, processing_status=CeleryStatus.STARTED)

    try:
        logger.info(f"Начало обработки данных сеанса {session_id}")

        with SyncSessionLocal() as db:
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                logger.error(f"Session {session_id} not found")
                update_session_fields(session_id, processing_status=CeleryStatus.FAILURE, processing_task_id=None)
                return {"status": "finished", "session_id": session_id}

            # --- Удаляем старые reconstructed карты и их файлы ---
            old_recs = db.query(ReconstructedImage).filter(ReconstructedImage.session_id == session_id).all()
            for rec in old_recs:
                relative_path = rec.file_path.removeprefix(settings.media.reconstructed_images_url).lstrip("/")
                file_path = os.path.join(settings.media.reconstructed_images_path, relative_path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Ошибка при удалении файла {file_path}: {e}")

            db.query(ReconstructedImage).filter(ReconstructedImage.session_id == session_id).delete(synchronize_session=False)
            db.commit()

            # Основная обработка
            result = analyze_hyperspectral_session(db, session)

            if result is None:
                cleanup_session_results_if_no_raw_images(session_id, db)
                logger.info(f"Результаты сеанса {session_id} очищены, анализ не выполнен.")
                update_session_fields(session_id, processing_status=CeleryStatus.RETRY, processing_task_id=None)
                return {"status": "finished", "session_id": session_id}

            # --- Сохраняем reconstructed карты ---
            for rec in result['reconstructed_images']:
                db.add(ReconstructedImage(
                    session_id=session_id,
                    chromophore_id=rec['chromophore_id'],
                    file_path=rec['file_path']
                ))

            # --- Сохраняем результат анализа (обновление если есть) ---
            existing = db.query(Result).filter(Result.session_id == session_id).first()
            if existing:
                existing.contour_path = result['contour_path']
                existing.s_coefficient = result['s_coefficient']
                existing.mean_lesion_thb = result['mean_lesion_thb']
                existing.mean_skin_thb = result['mean_skin_thb']
            else:
                db.add(Result(
                    session_id=session_id,
                    contour_path=result['contour_path'],
                    s_coefficient=result['s_coefficient'],
                    mean_lesion_thb=result['mean_lesion_thb'],
                    mean_skin_thb=result['mean_skin_thb'],
                ))

            db.commit()

        logger.info(f"Обработка сеанса {session_id} завершена")

        update_session_fields(
            session_id,
            processing_status=CeleryStatus.SUCCESS,
            processing_task_id=None
        )

    except Exception as exc:
        logger.exception(f"Ошибка при обработке сеанса {session_id}: {exc}")
        update_session_fields(
            session_id,
            processing_status=CeleryStatus.FAILURE,
            processing_task_id=None
        )
        raise

    return {"status": "finished", "session_id": session_id}
