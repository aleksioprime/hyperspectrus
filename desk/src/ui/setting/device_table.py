"""
Виджет управления списком устройств.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

class DeviceTableWidget(QTableWidget):
    """
    Таблица для отображения и выбора устройств.
    """
    def __init__(self, parent=None):
        super().__init__(0, 1, parent)
        self.setHorizontalHeaderLabels(["Название"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)

    def fill(self, devices):
        """
        Заполняет таблицу устройствами.
        :param devices: список моделей Device
        """
        self.setRowCount(0)
        for d in devices:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(d.name))
        if self.rowCount() > 0:
            self.selectRow(0)
