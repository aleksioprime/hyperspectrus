"""
Виджет управления списком хромофоров.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox

from db.db import get_db_session
from db.models import Chromophore


class ChromophoreTableWidget(QTableWidget):
    """
    Таблица для отображения и выбора хромофоров.
    """
    def __init__(self, parent=None):
        super().__init__(0, 1, parent)
        self.setHorizontalHeaderLabels(["Название"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
        self.verticalHeader().setVisible(False)
        self._internal_fill = False
        self.cellChanged.connect(self.on_cell_changed)

    def fill(self, chromophores):
        """
        Заполняет таблицу хромофорами.
        :param chromophores: список моделей Chromophore
        """
        self._internal_fill = True
        self.chromophores_list = chromophores  # Store for use in cellChanged
        self.setRowCount(0)
        for c in chromophores:
            row = self.rowCount()
            self.insertRow(row)
            item = QTableWidgetItem(c.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable) # Make item editable
            self.setItem(row, 0, item)
        self._internal_fill = False
        if self.rowCount() > 0:
            self.selectRow(0)

    def on_cell_changed(self, row, column):
        if self._internal_fill or column != 0:  # Only handle changes in the first column (name)
            return

        if not hasattr(self, 'chromophores_list') or row >= len(self.chromophores_list):
            return

        chromophore_obj = self.chromophores_list[row]
        new_name = self.item(row, column).text().strip()

        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Название хромофора не может быть пустым.")
            self.blockSignals(True)
            self.item(row, column).setText(chromophore_obj.name)
            self.blockSignals(False)
            return

        if new_name == chromophore_obj.name:
            return # No change

        try:
            with get_db_session() as session:
                db_chromophore = session.get(Chromophore, chromophore_obj.id)
                if db_chromophore:
                    db_chromophore.name = new_name
                    db_chromophore.symbol = new_name # Also update symbol as per previous edit_chrom logic
                    session.commit()
                    # Update local object to reflect changes
                    chromophore_obj.name = new_name
                    chromophore_obj.symbol = new_name
                    # Notify parent to reload matrix
                    parent_widget = self.parent()
                    if parent_widget and hasattr(parent_widget, 'reload_matrix'):
                        parent_widget.reload_matrix()
                else:
                    QMessageBox.warning(self, "Ошибка", f"Хромофор с ID {chromophore_obj.id} не найден в базе данных.")
                    self.blockSignals(True)
                    self.item(row, column).setText(chromophore_obj.name)
                    self.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось обновить хромофор: {e}")
            self.blockSignals(True)
            self.item(row, column).setText(chromophore_obj.name)
            self.blockSignals(False)
