"""
Виджет матрицы коэффициентов перекрытия спектр-хромофор.
"""
import random

from PyQt6.QtWidgets import QTableWidget, QDoubleSpinBox, QMessageBox, QAbstractSpinBox
from PyQt6.QtCore import Qt

from db.db import get_db_session
from db.models import OverlapCoefficient

class MatrixTableWidget(QTableWidget):
    """
    Матрица коэффициентов перекрытия спектр × хромофор.
    Автоматически сохраняет изменения в базу при редактировании.
    """
    def __init__(self, parent=None):
        super().__init__(0, 0, parent)
        self._internal_fill = False
        self._spinbox_map = {}  # (row, col): spinbox
        self._coefs_map = {}    # (row, col): (spectrum_id, chromophore_id)
        self.spectra = []
        self.chromophores = []

    def fill(self, spectra, chromophores, coefs):
        """
        Заполняет матрицу коэффициентов
        """
        self._internal_fill = True
        self.spectra = spectra
        self.chromophores = chromophores
        self.setRowCount(len(spectra))
        self.setColumnCount(len(chromophores))
        self.setHorizontalHeaderLabels([c.name for c in chromophores])
        self.setVerticalHeaderLabels([str(s.wavelength) for s in spectra])
        self._spinbox_map.clear()
        self._coefs_map.clear()

        for i, s in enumerate(spectra):
            for j, c in enumerate(chromophores):
                val = coefs.get((s.id, c.id), 0.0)
                spin = QDoubleSpinBox()
                spin.setRange(0, 1000)
                spin.setDecimals(4)
                spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
                spin.setValue(val)
                # Убираем выделение текста при фокусе (чтобы не было случайных багов)
                spin.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
                spin.valueChanged.connect(lambda new_val, row=i, col=j: self.on_spinbox_changed(row, col, new_val))
                self.setCellWidget(i, j, spin)
                self._spinbox_map[(i, j)] = spin
                self._coefs_map[(i, j)] = (s.id, c.id)

        self._internal_fill = False

    def on_spinbox_changed(self, row, col, new_val):
        if self._internal_fill:
            return
        # Валидация: только от 0 до 1000 (float)
        if not (0.0 <= new_val <= 1000.0):
            QMessageBox.warning(self, "Ошибка", "Коэффициент должен быть в диапазоне от 0 до 1000.")
            self._internal_fill = True
            # Вернуть к предыдущему значению
            spin = self._spinbox_map[(row, col)]
            spin.setValue(0.0 if new_val < 0 else 1000.0)
            self._internal_fill = False
            return

        spectrum_id, chromophore_id = self._coefs_map[(row, col)]

        # Запись в базу данных
        try:
            with get_db_session() as session:
                coef = session.query(OverlapCoefficient).filter_by(
                    spectrum_id=spectrum_id,
                    chromophore_id=chromophore_id
                ).first()
                if coef:
                    coef.coefficient = float(new_val)
                else:
                    coef = OverlapCoefficient(
                        spectrum_id=spectrum_id,
                        chromophore_id=chromophore_id,
                        coefficient=float(new_val)
                    )
                    session.add(coef)
                session.commit()

                # Проверяем, что записалось правильно
                checked_coef = session.query(OverlapCoefficient).filter_by(
                    spectrum_id=spectrum_id,
                    chromophore_id=chromophore_id
                ).first()
                if not checked_coef or abs(checked_coef.coefficient - float(new_val)) > 1e-6:
                    raise Exception("Ошибка подтверждения записи в базе")

        except Exception as e:
            QMessageBox.warning(self, "Ошибка сохранения", f"Не удалось сохранить коэффициент: {e}")
            # Откат значения в spinbox на старое (из базы, либо 0.0)
            self._internal_fill = True
            old_val = 0.0
            try:
                with get_db_session() as session:
                    coef = session.query(OverlapCoefficient).filter_by(
                        spectrum_id=spectrum_id,
                        chromophore_id=chromophore_id
                    ).first()
                    if coef:
                        old_val = coef.coefficient
            except Exception:
                pass
            self._spinbox_map[(row, col)].setValue(old_val)
            self._internal_fill = False

    def set_random_values(self, min_value=0.0, max_value=1.0, decimals=4):
        """Заполнить матрицу случайными значениями."""
        self._internal_fill = True
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                val = round(random.uniform(min_value, max_value), decimals)
                widget = self.cellWidget(i, j)
                if widget is not None:
                    widget.setValue(val)
                else:
                    item = self.item(i, j)
                    if item is not None:
                        item.setText(f"{val:.{decimals}f}")
        self._internal_fill = False
