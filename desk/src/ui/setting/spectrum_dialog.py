from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QSpinBox


class AddSpectrumDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить спектр")

        form = QFormLayout(self)

        self.wave_spin = QSpinBox()
        self.wave_spin.setRange(200, 1100)
        self.wave_spin.setValue(600)
        form.addRow("Длина волны (нм):", self.wave_spin)

        self.r_spin = QSpinBox()
        self.r_spin.setRange(0, 255)
        form.addRow("R:", self.r_spin)

        self.g_spin = QSpinBox()
        self.g_spin.setRange(0, 255)
        form.addRow("G:", self.g_spin)

        self.b_spin = QSpinBox()
        self.b_spin.setRange(0, 255)
        form.addRow("B:", self.b_spin)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        form.addRow(self.button_box)

    def get_values(self):
        return (
            self.wave_spin.value(),
            self.r_spin.value(),
            self.g_spin.value(),
            self.b_spin.value(),
        )