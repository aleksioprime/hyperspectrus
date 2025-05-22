"""
Виджет управления списком устройств.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox

from db.db import get_db_session
from db.models import Device


class DeviceTableWidget(QTableWidget):
    """
    Таблица для отображения и выбора устройств.
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

    def fill(self, devices):
        """
        Заполняет таблицу устройствами.
        :param devices: список моделей Device
        """
        self._internal_fill = True
        self.devices_list = devices  # Store for use in cellChanged
        self.setRowCount(0)
        for d in devices:
            row = self.rowCount()
            self.insertRow(row)
            name_item = QTableWidgetItem(d.name)
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)  # Make item editable
            self.setItem(row, 0, name_item)
        self._internal_fill = False
        if self.rowCount() > 0:
            self.selectRow(0)

    def on_cell_changed(self, row, column):
        if self._internal_fill or column != 0:  # Only handle changes in the first column (name)
            return

        if not hasattr(self, 'devices_list') or row >= len(self.devices_list):
            # This can happen if the table is cleared or the row index is out of bounds
            return

        device_obj = self.devices_list[row]
        new_name = self.item(row, column).text().strip()

        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Название устройства не может быть пустым.")
            # Revert to old name
            self.blockSignals(True)
            self.item(row, column).setText(device_obj.name)
            self.blockSignals(False)
            return

        if new_name == device_obj.name:
            return # No change

        try:
            with get_db_session() as session:
                db_device = session.get(Device, device_obj.id)
                if db_device:
                    db_device.name = new_name
                    session.commit()
                    device_obj.name = new_name # Update the name in the local list as well
                else:
                    QMessageBox.warning(self, "Ошибка", f"Устройство с ID {device_obj.id} не найдено в базе данных.")
                    # Revert to old name
                    self.blockSignals(True)
                    self.item(row, column).setText(device_obj.name)
                    self.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось обновить устройство: {e}")
            # Revert to old name
            self.blockSignals(True)
            self.item(row, column).setText(device_obj.name)
            self.blockSignals(False)
