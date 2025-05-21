"""
Виджет матрицы коэффициентов перекрытия спектр-хромофор.
"""

from PyQt6.QtWidgets import QTableWidget, QDoubleSpinBox

class MatrixWidget(QTableWidget):
    """
    Матрица коэффициентов перекрытия спектр × хромофор.
    """
    def __init__(self, parent=None):
        super().__init__(0, 0, parent)

    def fill(self, spectra, chromophores, coefs):
        """
        Заполняет матрицу коэффициентов.
        :param spectra: список моделей Spectrum
        :param chromophores: список моделей Chromophore
        :param coefs: dict (spectrum_id, chromophore_id) -> coefficient
        """
        self.setRowCount(len(spectra))
        self.setColumnCount(len(chromophores))
        self.setHorizontalHeaderLabels([c.name for c in chromophores])
        self.setVerticalHeaderLabels([str(s.wavelength) for s in spectra])

        self.matrix_data = []  # для связи с формой сохранения
        for i, s in enumerate(spectra):
            row = []
            for j, c in enumerate(chromophores):
                val = coefs.get((s.id, c.id), 0.0)
                spin = QDoubleSpinBox()
                spin.setRange(0, 1000)
                spin.setDecimals(4)
                spin.setValue(val)
                self.setCellWidget(i, j, spin)
                row.append(spin)
            self.matrix_data.append((s, row))
