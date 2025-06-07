import logging
from PyQt6.QtWidgets import QDialog, QFormLayout, QDateEdit, QComboBox, QListWidget, QTextEdit, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QDate, Qt, QTimer

from sqlalchemy.orm import joinedload
from db.db import get_db_session
from db.models import DeviceBinding, Device
from ui.patient.device_worker import DeviceStatusWorker

logger = logging.getLogger(__name__)

class SessionDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать сеанс")
        self.user = user
        layout = QFormLayout(self)
        logger.debug("SessionDialog __init__ started")

        # --- Worker для статуса устройства ---
        self._status_worker = DeviceStatusWorker()
        self._status_worker.finished.connect(self.on_device_status_checked)
        self._status_worker.error.connect(self.on_device_status_error)

        # --- Таймер статуса ---
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(3000)
        self.status_timer.timeout.connect(self.check_device_status)
        self.status_timer.start()
        logger.debug("Status timer started")

        # --- Поля выбора ---
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())

        self.device_combo = QComboBox()
        self.device_status_icon = QLabel("⏳")
        device_combo_layout = QHBoxLayout()
        device_combo_layout.addWidget(self.device_combo)
        device_combo_layout.addWidget(self.device_status_icon)

        with get_db_session() as session:
            self.devices = (
                session.query(DeviceBinding)
                .options(joinedload(DeviceBinding.device))
                .filter_by(user_id=str(user.id))
                .all()
            )

        for d in self.devices:
            self.device_combo.addItem(f"{d.device.name} ({d.ip_address})", d.id)

        self.spectra_list = QListWidget()
        self.spectra_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.spectra_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.spectra_list.setMaximumHeight(80)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)

        layout.addRow("Дата сеанса:", self.date_edit)
        layout.addRow("Устройство:", device_combo_layout)
        layout.addRow("Спектры:", self.spectra_list)
        layout.addRow("Заметки:", self.notes_edit)

        # --- Кнопки ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("Создать")
        self.cancel_btn = QPushButton("Отмена")
        self.save_btn.setEnabled(False)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addRow(btn_row)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.device_combo.currentIndexChanged.connect(self.update_spectra_list)
        self.device_combo.currentIndexChanged.connect(self.check_device_status)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)

        self.update_spectra_list()
        logger.debug("SessionDialog __init__ finished")

    def update_spectra_list(self):
        idx = self.device_combo.currentIndex()
        self.spectra_list.clear()
        if idx < 0 or not self.devices:
            self.spectra = []
            return
        device_binding = self.devices[idx]
        with get_db_session() as session:
            device = session.query(Device).options(joinedload(Device.spectra)).get(device_binding.device_id)
            self.spectra = list(device.spectra)
        for s in self.spectra:
            self.spectra_list.addItem(f"{s.wavelength} ({s.rgb_r}, {s.rgb_g}, {s.rgb_b})")
        self.check_device_status()

    def check_device_status(self):
        logger.debug("check_device_status called")
        idx = self.device_combo.currentIndex()
        if idx < 0 or not self.devices:
            logger.debug("No device selected or no devices available.")
            self.device_status_icon.setText("⏳")
            self.save_btn.setEnabled(False)
            return

        ip = self.devices[idx].ip_address
        # Прерываем старый запрос, если есть
        self._status_worker.abort()
        logger.debug(f"Запуск проверки устройства: {ip}")
        self.save_btn.setEnabled(False)
        self._status_worker.check(ip)

    def on_device_status_checked(self, ip, status):
        logger.debug(f"on_device_status_checked: IP={ip}, status={status}")
        if status == 'online':
            self.device_status_icon.setText("🟢")
            self.save_btn.setEnabled(True)
        else:
            self.device_status_icon.setText("🔴")
            self.save_btn.setEnabled(False)

    def on_device_status_error(self, ip, message):
        logger.error(f"on_device_status_error: IP={ip}, error={message}")

    def get_data(self):
        bdate = self.date_edit.date()
        idx = self.device_combo.currentIndex()
        device_binding = self.devices[idx] if idx >= 0 and self.devices else None
        return {
            "date": bdate.toPyDate() if bdate.isValid() else None,
            "device_binding": device_binding,
            "spectra": self.spectra,
            "notes": self.notes_edit.toPlainText().strip()
        }

    def on_device_changed(self):
        self.check_device_status()
        self.status_timer.start()

    def closeEvent(self, event):
        logger.debug("closeEvent called")
        self.status_timer.stop()
        self._status_worker.abort()
        logger.debug("closeEvent finished")
        super().closeEvent(event)
