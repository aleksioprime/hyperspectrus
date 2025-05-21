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
        self.download_photos_btn.clicked.connect(self.download_photos)
        self.process_btn.clicked.connect(self.process_results)

        # --- Инициализация данных ---
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

    def download_photos(self):
        """
        Скачивает фото через API устройства, сохраняет их в отдельную папку для каждой сессии,
        добавляет записи в таблицу RawImage с указанием spectrum_id.
        """
        if self.task_id is None:
            QMessageBox.warning(self, "Ошибка", "ID задачи не найден")
            return
        try:
            url = f"{self.device_api_url}/tasks/{self.task_id}/photos"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            photos = resp.json()
            saved_count = 0
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            photos_root = os.path.join(base_dir, "downloaded_photos")
            session_dir = os.path.join(photos_root, f"session_{self.session.id}")
            os.makedirs(session_dir, exist_ok=True)
            session_db = SessionLocal()
            for photo in photos:
                spectrum_id = photo.get("spectrum_id")
                # Проверяем, не существует ли уже такой снимок в базе
                exists = session_db.query(RawImage).filter_by(session_id=self.session.id, spectrum_id=spectrum_id).first()
                if exists:
                    continue
                # Скачиваем фото
                download_url = f"{self.device_api_url}/{photo.get('download_url')}"
                if not download_url:
                    continue
                img_resp = requests.get(download_url, timeout=20)
                if img_resp.status_code == 200:
                    fname = os.path.join(session_dir, f"spectrum_{spectrum_id}.jpg")
                    with open(fname, "wb") as f:
                        f.write(img_resp.content)
                    raw_image = RawImage(
                        session_id=self.session.id,
                        file_path=fname,
                        spectrum_id=spectrum_id
                    )
                    session_db.add(raw_image)
                    saved_count += 1
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось скачать фото с spectrum_id={spectrum_id}")
            session_db.commit()
            session_db.close()
            QMessageBox.information(self, "Готово", f"Загружено фото: {saved_count}")
            self.load_raw_photos()
            self.process_btn.setEnabled(self.has_photos())
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки фото: {e}")


    def process_results(self):
        """
        Расчет концентраций всех хромофоров, сегментация, сохранение.
        """

        db = SessionLocal()

        # 1. Получаем все raw-фото для этой сессии, отсортированные по длине волны
        raw_images = (
            db.query(RawImage)
            .filter_by(session_id=self.session.id)
            .options(joinedload(RawImage.spectrum))
            .all()
        )
        if not raw_images:
            QMessageBox.warning(self, "Нет фото", "Сначала загрузите снимки с устройства!")
            db.close()
            return

        raw_images = sorted(raw_images, key=lambda x: x.spectrum.wavelength)
        n_spectra = len(raw_images)
        # Проверяем размер всех картинок
        shapes = [Image.open(ri.file_path).size for ri in raw_images]
        if len(set(shapes)) != 1:
            QMessageBox.warning(self, "Ошибка", "Все снимки должны быть одного размера!")
            db.close()
            return
        W, H = shapes[0]

        # 2. Сборка гиперкуба (n_spectra, H, W)
        cube = np.stack(
            [np.array(Image.open(ri.file_path).convert("L"), dtype=np.float32) for ri in raw_images],
            axis=0
        )
        # 3. Получаем коэффициенты перекрытия (матрицу) для всех спектров и хромофоров
        chromophores = db.query(Chromophore).order_by(Chromophore.id).all()
        n_chroms = len(chromophores)
        overlap_matrix = np.zeros((n_spectra, n_chroms), dtype=np.float32)
        for i, ri in enumerate(raw_images):
            for j, chrom in enumerate(chromophores):
                coef = (
                    db.query(OverlapCoefficient)
                    .filter_by(spectrum_id=ri.spectrum_id, chromophore_id=chrom.id)
                    .first()
                )
                overlap_matrix[i, j] = coef.coefficient if coef else 0.0

        # 4. Ищем референс-снимки (например, через device_binding или шаблон). Если нет — делаем без референса
        # (Можно добавить поиск сессии-калибровки по patient/device_binding)
        ref_cube = None
        ref_found = False
        # Попробуем искать в отдельной папке или по специальной сессии
        # ref_images = ...
        # if ref_images: ref_cube = ...

        # 5. Преобразуем к оптической плотности (OD)
        cube_norm = np.clip(cube / 255.0, 1e-6, 1.0)
        OD = -np.log10(cube_norm)
        # Если есть референс:
        # OD = -np.log10(cube_norm / (ref_cube / 255.0))

        # 6. Вычисляем концентрации всех хромофоров
        concentration_maps = np.zeros((n_chroms, H, W), dtype=np.float32)
        for y in range(H):
            for x in range(W):
                y_vec = OD[:, y, x]
                try:
                    # Решаем переопределенную систему (Ax = y) через np.linalg.lstsq
                    x_vec, *_ = np.linalg.lstsq(overlap_matrix, y_vec, rcond=None)
                    concentration_maps[:, y, x] = x_vec
                except Exception:
                    concentration_maps[:, y, x] = 0

        # 7. Суммируем Hb + HbO2 (пример: символы "Hb" и "HbO2")
        idx_hbo2 = next((i for i, c in enumerate(chromophores) if c.symbol.lower() in ["hbo2", "hb02"]), None)
        idx_hb = next((i for i, c in enumerate(chromophores) if c.symbol.lower() == "hb"), None)
        if idx_hbo2 is not None and idx_hb is not None:
            thb_map = np.abs(concentration_maps[idx_hbo2]) + np.abs(concentration_maps[idx_hb])
        else:
            thb_map = np.abs(concentration_maps[0])  # fallback, если нет обоих

        # 8. Сегментация по Otsu (делим на очаг и кожу)
        thb_norm = (thb_map - np.nanmin(thb_map)) / (np.nanmax(thb_map) - np.nanmin(thb_map) + 1e-8)
        thb_img_uint8 = (thb_norm * 255).astype(np.uint8)
        try:
            threshold = threshold_otsu(thb_img_uint8)
        except Exception:
            threshold = 128
        mask_lesion = thb_img_uint8 >= threshold
        mask_skin = thb_img_uint8 < threshold

        # 9. Статистики
        mean_lesion = float(np.nanmean(thb_map[mask_lesion])) if np.any(mask_lesion) else 0.0
        mean_skin = float(np.nanmean(thb_map[mask_skin])) if np.any(mask_skin) else 0.0
        s_coefficient = mean_lesion / mean_skin if mean_skin > 0 else 0.0

        # 10. Сохраняем изображения (THb и сегментация)
        session_dir = os.path.join(
            os.path.dirname(raw_images[0].file_path), f"processed_{self.session.id}"
        )
        os.makedirs(session_dir, exist_ok=True)
        thb_img_path = os.path.join(session_dir, "thb_map.png")
        Image.fromarray((thb_norm * 255).astype(np.uint8)).save(thb_img_path)
        mask_img_path = os.path.join(session_dir, "mask_otsu.png")
        Image.fromarray((mask_lesion * 255).astype(np.uint8)).save(mask_img_path)

        # 11. Удаляем старые записи из базы и сохраняем ReconstructedImage для каждого хромофора
        old_imgs = db.query(ReconstructedImage).filter_by(session_id=self.session.id).all()
        for old_img in old_imgs:
            try:
                if os.path.isfile(old_img.file_path):
                    os.remove(old_img.file_path)  # Удалить старый файл (если есть)
            except Exception as e:
                print(f"Не удалось удалить файл {old_img.file_path}: {e}")
            db.delete(old_img)
        db.flush()  # чтобы гарантировать удаление перед добавлением новых

        for i, chrom in enumerate(chromophores):
            img_path = os.path.join(session_dir, f"{chrom.symbol}.png")
            img_norm = (concentration_maps[i] - np.nanmin(concentration_maps[i])) / (
                np.nanmax(concentration_maps[i]) - np.nanmin(concentration_maps[i]) + 1e-8
            )
            Image.fromarray((img_norm * 255).astype(np.uint8)).save(img_path)
            rec_img = ReconstructedImage(
                id=str(uuid.uuid4()),
                session_id=self.session.id,
                chromophore_id=chrom.id,
                file_path=img_path,
            )
            db.add(rec_img)

        # 12. Сохраняем результат (Result)
        old_result = db.query(Result).filter_by(session_id=self.session.id).first()
        if old_result:
            db.delete(old_result)
            db.flush()

        result_obj = Result(
            id=str(uuid.uuid4()),
            session_id=self.session.id,
            contour_path=mask_img_path,
            thb_path=thb_img_path,
            s_coefficient=s_coefficient,
            mean_lesion_thb=mean_lesion,
            mean_skin_thb=mean_skin,
            notes="Автоматическая обработка"
        )
        db.add(result_obj)
        db.commit()
        db.close()

        self.load_proc_photos()

        QMessageBox.information(
            self, "Обработка",
            f"Готово!\nS-коэффициент: {s_coefficient:.2f}\nTHb (очаг): {mean_lesion:.2f}\nTHb (кожа): {mean_skin:.2f}"
        )
        self.refresh_session_data()


    def showEvent(self, event):
        super().showEvent(event)
        # Центрируем окно
        screen = self.screen().availableGeometry()
        size = self.frameGeometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        """
        Действия при закрытии окна (если потребуется).
        """
        event.accept()
