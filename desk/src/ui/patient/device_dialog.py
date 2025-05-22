from sqlalchemy.orm import joinedload

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QComboBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt


from db.db import SessionLocal
from db.models import Device, DeviceBinding


class DeviceBindingDialog(QDialog):
    """Окно для управления IP устройств пользователя с возможностью редактирования IP-адреса."""
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Мои устройства и IP")
        self.setMinimumWidth(700)
        self.user = user
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Устройство", "IP-адрес"])
        self.table.setColumnWidth(1, 30)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.add_btn = QPushButton("Добавить")
        self.del_btn = QPushButton("Удалить")
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)
        layout.addLayout(btn_row)

        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_binding)
        self.table.cellChanged.connect(self.save_cell_change)
        self.table.selectionModel().selectionChanged.connect(self.update_del_btn)

        self.devices = []
        self.bindings = []
        self._adding_row = False

        self.reload()

    def reload(self):
        self.table.blockSignals(True)
        session = SessionLocal()
        self.devices = session.query(Device).all()
        self.bindings = (
            session.query(DeviceBinding)
            .filter_by(user_id=str(self.user.id))
            .options(joinedload(DeviceBinding.device))
            .all()
        )
        session.close()
        self.table.setRowCount(0)

        for b in self.bindings:
            self.table.insertRow(self.table.rowCount())
            row = self.table.rowCount() - 1
            # Название устройства (не редактируется)
            device_item = QTableWidgetItem(b.device.name if b.device else "")
            device_item.setFlags(device_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, device_item)
            # IP-адрес (редактируемый)
            ip_item = QTableWidgetItem(b.ip_address or "")
            ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, ip_item)

        self.table.blockSignals(False)
        self._adding_row = False
        self.add_btn.setEnabled(True)
        self.update_del_btn()

    def add_row(self):
        if self._adding_row:
            return
        row = self.table.rowCount()
        self.table.insertRow(row)
        combo = QComboBox()
        for dev in self.devices:
            combo.addItem(dev.name, str(dev.id))
        self.table.setCellWidget(row, 0, combo)
        ip_item = QTableWidgetItem("")
        ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, ip_item)
        self._adding_row = True
        self.add_btn.setEnabled(False)
        self.del_btn.setEnabled(False)
        self.table.setCurrentCell(row, 1)
        self.table.editItem(self.table.item(row, 1))

    def save_cell_change(self, row, col):
        # Сохраняем новые/изменённые IP-адреса
        if self._adding_row and row == self.table.rowCount() - 1:
            # Добавление нового устройства
            combo = self.table.cellWidget(row, 0)
            ip_item = self.table.item(row, 1)
            device_idx = combo.currentIndex() if combo else -1
            ip = ip_item.text().strip() if ip_item else ""
            if device_idx < 0 or not ip:
                return
            device_id = self.devices[device_idx].id
            session = SessionLocal()
            existing = session.query(DeviceBinding).filter_by(
                user_id=str(self.user.id), device_id=device_id
            ).first()
            if existing:
                QMessageBox.warning(self, "Ошибка", "Это устройство уже связано с вами!")
                session.close()
                self.table.blockSignals(True)
                self.table.removeRow(row)
                self.table.blockSignals(False)
                self._adding_row = False
                self.add_btn.setEnabled(True)
                self.del_btn.setEnabled(self.table.rowCount() > 0)
                self.update_del_btn()
                return
            b = DeviceBinding(
                user_id=str(self.user.id),
                device_id=device_id,
                ip_address=ip,
            )
            session.add(b)
            session.commit()
            session.close()
            self.reload()
            return

        # Редактирование существующего IP
        if not self._adding_row and row < len(self.bindings) and col == 1:
            ip_item = self.table.item(row, 1)
            new_ip = ip_item.text().strip() if ip_item else ""
            binding = self.bindings[row]
            session = SessionLocal()
            db_binding = session.query(DeviceBinding).get(binding.id)
            if db_binding and new_ip != db_binding.ip_address:
                db_binding.ip_address = new_ip
                session.commit()
            session.close()
            # Не вызываем self.reload() — чтобы не сбивать фокус редактирования

    def update_del_btn(self):
        row = self.table.currentRow()
        enabled = (not self._adding_row) and row >= 0 and row < len(self.bindings)
        self.del_btn.setEnabled(enabled)

    def delete_binding(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.bindings):
            return
        b = self.bindings[row]
        reply = QMessageBox.question(
            self, "Удалить связь",
            f"Удалить устройство {b.device.name} с IP {b.ip_address}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            db = session.query(DeviceBinding).get(b.id)
            session.delete(db)
            session.commit()
            session.close()
            self.reload()
