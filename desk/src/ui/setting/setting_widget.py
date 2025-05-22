"""
Главное окно для управления устройствами, спектрами, хромофорами и матрицей коэффициентов перекрытия.
Связывает подчинённые виджеты и реализует бизнес-логику.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QInputDialog
)
from db.db import get_db_session
from db.models import Device, Spectrum, Chromophore, OverlapCoefficient

from ui.setting.device_table import DeviceTableWidget
from ui.setting.spectrum_table import SpectrumTableWidget
from ui.setting.chromophore_table import ChromophoreTableWidget
from ui.setting.matrix_table import MatrixTableWidget


class SettingWidget(QDialog):
    """
    Главное окно настроек оборудования.
    Включает управление:
    - устройствами,
    - спектрами,
    - хромофорами,
    - матрицей коэффициентов перекрытия.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки оборудования")
        self.setMinimumSize(1000, 600)

        layout = QHBoxLayout(self)

        # ====== Левая панель ======
        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("Устройства"))
        self.device_table = DeviceTableWidget()
        left_box.addWidget(self.device_table)
        dev_btns = QHBoxLayout()
        self.add_device_btn = QPushButton("Добавить")
        self.del_device_btn = QPushButton("Удалить")
        dev_btns.addWidget(self.add_device_btn)
        dev_btns.addWidget(self.del_device_btn)
        left_box.addLayout(dev_btns)

        left_box.addWidget(QLabel("Спектры"))
        self.spectrum_table = SpectrumTableWidget()
        left_box.addWidget(self.spectrum_table)
        spec_btns = QHBoxLayout()
        self.add_spectrum_btn = QPushButton("Добавить")
        self.del_spectrum_btn = QPushButton("Удалить")
        spec_btns.addWidget(self.add_spectrum_btn)
        spec_btns.addWidget(self.del_spectrum_btn)
        left_box.addLayout(spec_btns)

        left_box.addWidget(QLabel("Хромофоры"))
        self.chrom_table = ChromophoreTableWidget()
        left_box.addWidget(self.chrom_table)
        chrom_btns = QHBoxLayout()
        self.add_chrom_btn = QPushButton("Добавить")
        self.del_chrom_btn = QPushButton("Удалить")
        chrom_btns.addWidget(self.add_chrom_btn)
        chrom_btns.addWidget(self.del_chrom_btn)
        left_box.addLayout(chrom_btns)

        layout.addLayout(left_box, stretch=2)

        # ====== Матрица ======
        matrix_box = QVBoxLayout()
        matrix_box.addWidget(QLabel("Матрица коэффициентов перекрытия (Спектр × Хромофор)"))
        self.matrix_table = MatrixTableWidget()
        matrix_box.addWidget(self.matrix_table, stretch=1)
        self.save_matrix_btn = QPushButton("Сохранить коэффициенты")
        matrix_box.addWidget(self.save_matrix_btn)
        layout.addLayout(matrix_box, stretch=6)

        # ==== Связывание событий ====
        self.device_table.selectionModel().selectionChanged.connect(self.on_device_selected)
        self.spectrum_table.selectionModel().selectionChanged.connect(self.reload_matrix)
        self.spectrum_table.selectionModel().selectionChanged.connect(self.update_spectrum_buttons)
        self.chrom_table.selectionModel().selectionChanged.connect(self.reload_matrix)

        self.add_device_btn.clicked.connect(self.add_device)
        self.del_device_btn.clicked.connect(self.delete_device)
        self.add_spectrum_btn.clicked.connect(self.add_spectrum)
        self.del_spectrum_btn.clicked.connect(self.delete_spectrum)
        self.add_chrom_btn.clicked.connect(self.add_chrom)
        self.del_chrom_btn.clicked.connect(self.delete_chrom)
        self.save_matrix_btn.clicked.connect(self.save_matrix)

        # ==== Инициализация таблиц ====
        self.reload_devices()
        self.reload_chroms()
        self.reload_matrix()

    # ==== УСТРОЙСТВА ====
    def reload_devices(self):
        """
        Загружает устройства из БД и обновляет таблицу устройств.
        """
        with get_db_session() as session:
            self.devices = session.query(Device).all()
        self.device_table.fill(self.devices)
        self.on_device_selected()

    def get_selected_device(self):
        """
        Возвращает выбранное устройство (или None).
        """
        rows = self.device_table.selectionModel().selectedRows()
        if not rows:
            return None
        return self.devices[rows[0].row()]

    def add_device(self):
        """
        Диалог добавления нового устройства.
        """
        text, ok = QInputDialog.getText(self, "Добавить устройство", "Название устройства:")
        if ok and text:
            with get_db_session() as session:
                d = Device(name=text)
                session.add(d)
                session.commit()
            self.reload_devices()

    def delete_device(self):
        """
        Диалог удаления устройства.
        """
        d = self.get_selected_device()
        if not d:
            QMessageBox.warning(self, "Ошибка", "Выберите устройство для удаления.")
            return
        confirm = QMessageBox.question(self, "Удалить устройство?",
            f"Удалить устройство {d.name} и все его спектры?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            with get_db_session() as session:
                dev = session.get(Device, d.id)
                session.delete(dev)
                session.commit()
            self.reload_devices()

    # ==== СПЕКТРЫ ====
    def update_spectrum_buttons(self):
        selected = self.spectrum_table.selectionModel().hasSelection()
        self.edit_spectrum_btn.setEnabled(selected)
        self.del_spectrum_btn.setEnabled(selected)

    def reload_spectra(self):
        """
        Загружает спектры для выбранного устройства.
        """
        d = self.get_selected_device()
        if not d:
            self.spectrum_table.setRowCount(0)
            self.spectra = []
            return
        with get_db_session() as session:
            self.spectra = session.query(Spectrum).filter_by(device_id=d.id).order_by(Spectrum.wavelength).all()
        self.spectrum_table.fill(self.spectra)
        self.update_spectrum_buttons()

    def get_selected_spectrum(self):
        """
        Возвращает выбранный спектр (или None).
        """
        rows = self.spectrum_table.selectionModel().selectedRows()
        if not rows or not hasattr(self, 'spectra'):
            return None
        return self.spectra[rows[0].row()]

    def add_spectrum(self):
        """
        Диалог добавления нового спектра для устройства.
        """
        d = self.get_selected_device()
        if not d:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите устройство.")
            return
        w, ok = QInputDialog.getInt(self, "Длина волны", "Введите длину волны (нм):", min=200, max=1100)
        if ok:
            with get_db_session() as session:
                spec = Spectrum(device_id=d.id, wavelength=w)
                session.add(spec)
                session.commit()
            self.reload_spectra()
            self.reload_matrix()

    def delete_spectrum(self):
        """
        Диалог удаления спектра.
        """
        s = self.get_selected_spectrum()
        if not s:
            QMessageBox.warning(self, "Ошибка", "Выберите спектр для удаления.")
            return
        confirm = QMessageBox.question(self, "Удалить спектр?", "Удалить выбранный спектр?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            with get_db_session() as session:
                spec = session.get(Spectrum, s.id)
                session.delete(spec)
                session.commit()
            self.reload_spectra()
            self.reload_matrix()

    # ==== ХРОМОФОРЫ ====
    def reload_chroms(self):
        """
        Загружает хромофоры из БД.
        """
        with get_db_session() as session:
            self.chroms = session.query(Chromophore).order_by(Chromophore.name).all()
        self.chrom_table.fill(self.chroms)

    def get_selected_chrom(self):
        """
        Возвращает выбранный хромофор (или None).
        """
        rows = self.chrom_table.selectionModel().selectedRows()
        if not rows or not hasattr(self, 'chroms'):
            return None
        return self.chroms[rows[0].row()]

    def add_chrom(self):
        """
        Диалог добавления хромофора.
        """
        text, ok = QInputDialog.getText(self, "Добавить хромофор", "Название хромофора:")
        if ok and text:
            with get_db_session() as session:
                c = Chromophore(name=text, symbol=text)
                session.add(c)
                session.commit()
            self.reload_chroms()
            self.reload_matrix()

    def delete_chrom(self):
        """
        Диалог удаления хромофора.
        """
        c = self.get_selected_chrom()
        if not c:
            QMessageBox.warning(self, "Ошибка", "Выберите хромофор для удаления.")
            return
        confirm = QMessageBox.question(self, "Удалить хромофор?", "Удалить выбранный хромофор?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            with get_db_session() as session:
                chrom = session.get(Chromophore, c.id)
                session.delete(chrom)
                session.commit()
            self.reload_chroms()
            self.reload_matrix()

    # ==== МАТРИЦА КОЭФФИЦИЕНТОВ ====
    def reload_matrix(self):
        """
        Загружает матрицу коэффициентов для выбранного устройства.
        """
        d = self.get_selected_device()
        if not d:
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            return
        with get_db_session() as session:
            spectra = session.query(Spectrum).filter_by(device_id=d.id).order_by(Spectrum.wavelength).all()
            chromos = session.query(Chromophore).order_by(Chromophore.name).all()
            spectrum_ids = [s.id for s in spectra]
            coefs = {
                (c.spectrum_id, c.chromophore_id): c.coefficient
                for c in session.query(OverlapCoefficient).filter(
                    OverlapCoefficient.spectrum_id.in_(spectrum_ids)
                ).all()
            }
        self.matrix_table.fill(spectra, chromos, coefs)

    def save_matrix(self):
        """
        Сохраняет значения коэффициентов из матрицы в БД.
        """
        d = self.get_selected_device()
        if not d or not hasattr(self.matrix_table, "matrix_data"):
            return
        with get_db_session() as session:
            chromos = session.query(Chromophore).order_by(Chromophore.name).all()
            for i, (s, row) in enumerate(self.matrix_table.matrix_data):
                for j, spin in enumerate(row):
                    val = spin.value()
                    chrom_id = chromos[j].id
                    coef = session.query(OverlapCoefficient).filter_by(spectrum_id=s.id, chromophore_id=chrom_id).first()
                    if coef:
                        coef.coefficient = val
                    else:
                        coef = OverlapCoefficient(spectrum_id=s.id, chromophore_id=chrom_id, coefficient=val)
                        session.add(coef)
            session.commit()
        QMessageBox.information(self, "Готово", "Коэффициенты сохранены.")

    # ==== ВСПОМОГАТЕЛЬНОЕ ====
    def on_device_selected(self):
        """
        Слот: выбранное устройство изменилось — обновить спектры и матрицу.
        """
        self.reload_spectra()
        self.reload_matrix()
