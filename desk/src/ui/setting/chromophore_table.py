"""
Виджет управления списком хромофоров.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

class ChromophoreTableWidget(QTableWidget):
    """
    Таблица для отображения и выбора хромофоров.
    """
    def __init__(self, parent=None):
        super().__init__(0, 1, parent)
        self.setHorizontalHeaderLabels(["Название"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)

    def fill(self, chromophores):
        """
        Заполняет таблицу хромофорами.
        :param chromophores: список моделей Chromophore
        """
        self.setRowCount(0)
        for c in chromophores:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(c.name))
        if self.rowCount() > 0:
            self.selectRow(0)
