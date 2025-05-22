"""
Виджет управления спектрами: таблица для отображения и редактирования RGB-значений спектров с автосохранением в базу.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt
from db.db import SessionLocal
from db.models import Spectrum

class SpectrumTableWidget(QTableWidget):
    """
    Таблица для отображения и редактирования спектров.
    Позволяет редактировать RGB-значения прямо в таблице (двойной щелчок или Enter).
    """

    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Длина волны", "R", "G", "B"])
        self.setColumnWidth(0, 110)
        self.setColumnWidth(1, 40)
        self.setColumnWidth(2, 40)
        self.setColumnWidth(3, 40)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
        self.verticalHeader().setVisible(False)
        self.spectra = []
        # Сигнал cellChanged будет подключён только один раз
        self.cellChanged.connect(self.on_cell_changed)
        self._internal_fill = False  # Флаг, чтобы не срабатывать при заполнении таблицы

    def fill(self, spectra):
        """
        Заполняет таблицу спектрами.
        :param spectra: список моделей Spectrum
        """
        self._internal_fill = True  # Не реагируем на cellChanged во время fill
        self.spectra = spectra
        self.setRowCount(0)
        for s in spectra:
            row = self.rowCount()
            self.insertRow(row)
            # Длина волны
            wave_item = QTableWidgetItem(str(s.wavelength))
            wave_item.setFlags(wave_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, wave_item)
            # R, G, B
            for col, val in enumerate((s.rgb_r or 0, s.rgb_g or 0, s.rgb_b or 0), start=1):
                it = QTableWidgetItem(str(val))
                it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
                self.setItem(row, col, it)
        self._internal_fill = False
        if self.rowCount() > 0:
            self.selectRow(0)

    def on_cell_changed(self, row, col):
        """
        Слот: сохранение изменений RGB-значения спектра в базе при редактировании.
        """
        if self._internal_fill:
            return  # Не реагировать на события при заполнении таблицы
        # Только для столбцов R, G, B
        if col not in (1, 2, 3):
            return
        if not self.spectra or row >= len(self.spectra):
            return
        s = self.spectra[row]
        try:
            value = int(self.item(row, col).text())
            if not (0 <= value <= 255):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите целое число от 0 до 255.")
            # Возвращаем предыдущее значение
            self.blockSignals(True)
            if col == 1:
                self.item(row, col).setText(str(s.rgb_r or 0))
            elif col == 2:
                self.item(row, col).setText(str(s.rgb_g or 0))
            elif col == 3:
                self.item(row, col).setText(str(s.rgb_b or 0))
            self.blockSignals(False)
            return
        # Сохраняем в базу
        with SessionLocal() as session:
            spectrum = session.get(Spectrum, s.id)
            if col == 1:
                spectrum.rgb_r = value
                s.rgb_r = value
            elif col == 2:
                spectrum.rgb_g = value
                s.rgb_g = value
            elif col == 3:
                spectrum.rgb_b = value
                s.rgb_b = value
            session.commit()
