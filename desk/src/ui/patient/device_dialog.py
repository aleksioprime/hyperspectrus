from sqlalchemy.orm import joinedload
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QComboBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer

from db.db import get_db_session
from db.models import Device, DeviceBinding
from ui.patient.device_worker import DeviceStatusWorker

class DeviceBindingDialog(QDialog):
    """
    Диалог для управления списком устройств пользователя:
    позволяет добавлять, удалять устройства и отслеживать их статус через сеть.
    Статус проверяется асинхронно без потоков (QThread), только с QTimer и DeviceStatusWorker.
    """
    STATUS_CHECK_INTERVAL = 3000  # Интервал проверки статуса устройств в мс

    def __init__(self, user, parent=None):
        """
        Инициализация диалога, загрузка устройств и связей пользователя.
        """
        super().__init__(parent)
        self.setWindowTitle("Мои устройства и IP")
        self.setMinimumWidth(500)
        self.user = user
        layout = QVBoxLayout(self)

        # Основная таблица: Устройство | IP-адрес | Статус
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Устройство", "IP-адрес", "Статус"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Кнопки управления
        self.add_btn = QPushButton("Добавить")
        self.del_btn = QPushButton("Удалить")
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        self.save_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.back_btn = QPushButton("Назад")
        self.back_btn.clicked.connect(self.close)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.back_btn)
        layout.addLayout(btn_row)

        # Сигналы
        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_binding)
        self.save_btn.clicked.connect(self.save_row)
        self.cancel_btn.clicked.connect(self.cancel_add_row)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_change)
        self.table.cellChanged.connect(self.on_cell_changed)

        # Хранение устройств, связей и рабочих объектов
        self.devices = []
        self.bindings = []
        self._adding_row = False
        self.status_timers = dict()     # row => QTimer
        self.status_workers = dict()    # row => DeviceStatusWorker

        self.reload()

    def reload(self):
        """
        Загрузка устройств и связей пользователя, пересоздание таблицы и таймеров статуса.
        """
        self._stop_all_timers()
        self._abort_all_workers()
        self.table.blockSignals(True)
        with get_db_session() as session:
            self.devices = session.query(Device).all()
            self.bindings = (
                session.query(DeviceBinding)
                .filter_by(user_id=str(self.user.id))
                .options(joinedload(DeviceBinding.device))
                .all()
            )
        self.table.setRowCount(0)
        for i, b in enumerate(self.bindings):
            self.table.insertRow(self.table.rowCount())
            row = self.table.rowCount() - 1

            device_item = QTableWidgetItem(b.device.name if b.device else "")
            device_item.setFlags(device_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, device_item)

            ip_item = QTableWidgetItem(b.ip_address or "")
            ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, ip_item)

            status_item = QTableWidgetItem("⏳")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, status_item)

            self._setup_status_timer(b.ip_address, row)

        self.table.blockSignals(False)
        self._adding_row = False
        self.save_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.add_btn.setVisible(True)
        self.add_btn.setEnabled(True)
        self.del_btn.setVisible(True)
        self.update_del_btn()

    def _setup_status_timer(self, ip, row):
        """
        Настроить таймер для периодической проверки статуса устройства по IP.
        """
        def check():
            self.check_device_status_async(ip, row)
        timer = QTimer(self)
        timer.setInterval(self.STATUS_CHECK_INTERVAL)
        timer.timeout.connect(check)
        timer.start()
        self.status_timers[row] = timer
        check()  # Первая проверка сразу

    def _stop_all_timers(self):
        """Остановить и удалить все таймеры статуса."""
        for t in self.status_timers.values():
            t.stop()
            t.deleteLater()
        self.status_timers.clear()

    def _abort_all_workers(self):
        """Прервать все активные DeviceStatusWorker'ы."""
        for w in self.status_workers.values():
            w.abort()
            w.deleteLater()
        self.status_workers.clear()

    def check_device_status_async(self, ip, row):
        """
        Асинхронно проверить статус устройства по IP для строки row.
        Запускается при старте таймера и при редактировании IP.
        """
        if not ip:
            self.table.setItem(row, 2, QTableWidgetItem("—"))
            return

        # Если уже есть worker — отменяем предыдущий
        if row in self.status_workers:
            self.status_workers[row].abort()
            self.status_workers[row].deleteLater()

        worker = DeviceStatusWorker()
        self.status_workers[row] = worker

        def update_status(ip_checked, status):
            # Установить статус 🟢/🔴 в нужной строке
            item = self.table.item(row, 2)
            if item:
                item.setText("🟢" if status == 'online' else "🔴")
            worker.deleteLater()
            self.status_workers.pop(row, None)

        worker.finished.connect(update_status)
        worker.error.connect(lambda ip, msg: update_status(ip, 'offline'))
        worker.check(ip)  # Асинхронно (без потоков!)

    def add_row(self):
        """
        Начать добавление новой строки (связки устройство-IP).
        """
        if self._adding_row:
            return
        # self.table.setFocus()
        row = self.table.rowCount()
        self.table.insertRow(row)
        combo = QComboBox()
        for dev in self.devices:
            combo.addItem(dev.name, str(dev.id))
        self.table.setCellWidget(row, 0, combo)
        ip_item = QTableWidgetItem("")
        ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, ip_item)
        status_item = QTableWidgetItem("—")
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 2, status_item)

        self._adding_row = True
        self.add_btn.setVisible(False)
        self.del_btn.setVisible(False)
        self.save_btn.setVisible(True)
        self.cancel_btn.setVisible(True)
        self.table.setCurrentCell(row, 1)
        self.table.editItem(self.table.item(row, 1))

    def cancel_add_row(self):
        """
        Отмена добавления новой строки.
        """
        if self._adding_row:
            self.table.blockSignals(True)
            self.table.removeRow(self.table.rowCount() - 1)
            self.table.blockSignals(False)
            self._adding_row = False
            self.save_btn.setVisible(False)
            self.cancel_btn.setVisible(False)
            self.add_btn.setVisible(True)
            self.add_btn.setEnabled(True)
            self.del_btn.setVisible(True)
            self.update_del_btn()

    def save_row(self):
        """
        Сохранение новой строки: добавление новой связи в базу.
        """
        if not self._adding_row:
            return
        row = self.table.rowCount() - 1
        combo = self.table.cellWidget(row, 0)
        ip_item = self.table.item(row, 1)
        device_idx = combo.currentIndex() if combo else -1
        ip = ip_item.text().strip() if ip_item else ""
        if device_idx < 0 or not ip:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        device_id = self.devices[device_idx].id
        with get_db_session() as session:
            existing = session.query(DeviceBinding).filter_by(
                user_id=str(self.user.id), device_id=device_id
            ).first()
            if existing:
                QMessageBox.warning(self, "Ошибка", "Это устройство уже связано с вами!")
                self.cancel_add_row()
                return
            b = DeviceBinding(
                user_id=str(self.user.id),
                device_id=device_id,
                ip_address=ip,
            )
            session.add(b)
            session.commit()
        self.reload()

    def on_cell_changed(self, row, col):
        """
        Обработка изменения ячейки: при изменении IP инициируем новую проверку статуса.
        """
        if not self._adding_row and row < len(self.bindings) and col == 1:
            ip_item = self.table.item(row, 1)
            new_ip = ip_item.text().strip() if ip_item else ""
            binding = self.bindings[row]
            with get_db_session() as session:
                db_binding = session.query(DeviceBinding).get(binding.id)
                if db_binding and new_ip != db_binding.ip_address:
                    db_binding.ip_address = new_ip
                    session.commit()
            # Перезапустить таймер проверки статуса
            if row in self.status_timers:
                self.status_timers[row].stop()
                self.status_timers[row].start()
            self.table.setItem(row, 2, QTableWidgetItem("⏳"))
            self.check_device_status_async(new_ip, row)

    def on_selection_change(self, selected, deselected):
        """Обновить состояние кнопки удаления при смене выбора."""
        self.update_del_btn()

    def update_del_btn(self):
        """Включить/отключить кнопку удаления в зависимости от выделения строк."""
        rows = self.table.selectionModel().selectedRows()
        enabled = (
            not self._adding_row
            and len(rows) > 0
            and all(row.row() < len(self.bindings) for row in rows)
        )
        self.del_btn.setEnabled(enabled)

    def delete_binding(self):
        """
        Удаление связи: подтверждение и удаление из базы.
        """
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        if row < 0 or row >= len(self.bindings):
            return
        b = self.bindings[row]
        reply = QMessageBox.question(
            self, "Удалить связь",
            f"Удалить устройство {b.device.name} с IP {b.ip_address}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            with get_db_session() as session:
                db = session.query(DeviceBinding).get(b.id)
                session.delete(db)
                session.commit()
            self.reload()

    def closeEvent(self, event):
        """
        При закрытии окна: остановить все таймеры и отменить все проверки.
        """
        self._stop_all_timers()
        self._abort_all_workers()
        super().closeEvent(event)
