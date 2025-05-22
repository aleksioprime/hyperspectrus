"""
Виджет управления спектрами: таблица для отображения и редактирования RGB-значений спектров с автосохранением в базу.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt

from db.db import get_db_session
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
            wave_item.setFlags(wave_item.flags() | Qt.ItemFlag.ItemIsEditable) # Make wavelength editable
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
        if self._internal_fill:
            return
        
        if not self.spectra or row >= len(self.spectra):
            return
        
        s = self.spectra[row]
        
        if col == 0: # Wavelength
            try:
                value = int(self.item(row, col).text())
                if not (200 <= value <= 1100): # Validation range
                    QMessageBox.warning(self, "Ошибка", "Длина волны должна быть в диапазоне 200-1100 нм.")
                    raise ValueError("Invalid range")
            except ValueError as e:
                self.blockSignals(True)
                self.item(row, col).setText(str(s.wavelength))
                self.blockSignals(False)
                if "Invalid range" not in str(e): # Avoid double message if it's our specific error
                     QMessageBox.warning(self, "Ошибка", "Введите целое число для длины волны.")
                return

            if s.wavelength == value: # No change
                return

            with get_db_session() as session:
                spectrum = session.get(Spectrum, s.id)
                if spectrum:
                    spectrum.wavelength = value
                    session.commit()
                    s.wavelength = value # Update local cache
                    
                    # Notify parent to reload matrix
                    parent_widget = self.parent() 
                    if parent_widget and hasattr(parent_widget, 'reload_matrix'):
                        parent_widget.reload_matrix() 
                else:
                    QMessageBox.warning(self, "Ошибка", "Спектр не найден в базе данных.") # Changed to warning
                    self.blockSignals(True)
                    self.item(row, col).setText(str(s.wavelength)) # Revert
                    self.blockSignals(False)

        elif col in (1, 2, 3): # R, G, B
            try:
                value = int(self.item(row, col).text())
                if not (0 <= value <= 255):
                    raise ValueError("Invalid RGB range")
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите целое число от 0 до 255.")
                self.blockSignals(True)
                if col == 1: self.item(row, col).setText(str(s.rgb_r or 0))
                elif col == 2: self.item(row, col).setText(str(s.rgb_g or 0))
                elif col == 3: self.item(row, col).setText(str(s.rgb_b or 0))
                self.blockSignals(False)
                return

            current_val = None
            if col == 1: current_val = s.rgb_r
            elif col == 2: current_val = s.rgb_g
            elif col == 3: current_val = s.rgb_b
            if current_val == value: return

            with get_db_session() as session:
                spectrum = session.get(Spectrum, s.id)
                if spectrum:
                    if col == 1: spectrum.rgb_r = value; s.rgb_r = value
                    elif col == 2: spectrum.rgb_g = value; s.rgb_g = value
                    elif col == 3: spectrum.rgb_b = value; s.rgb_b = value
                    session.commit()
                else:
                    QMessageBox.warning(self, "Ошибка", "Спектр не найден в базе данных при обновлении RGB.") # Changed to warning
                    self.blockSignals(True)
                    if col == 1: self.item(row, col).setText(str(s.rgb_r or 0))
                    elif col == 2: self.item(row, col).setText(str(s.rgb_g or 0))
                    elif col == 3: self.item(row, col).setText(str(s.rgb_b or 0))
                    self.blockSignals(False)
