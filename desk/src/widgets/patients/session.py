from PyQt6.QtWidgets import QDialog, QFormLayout, QDateEdit, QComboBox, QListWidget, QTextEdit, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QDate, Qt, QTimer
import requests
from sqlalchemy.orm import joinedload

from db.db import SessionLocal
from db.models import DeviceBinding, Device


class SessionDialog(QDialog):
    """
    Диалог для создания нового сеанса: выбор устройства, даты и спектров.
    """
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать сеанс")
        self.user = user
        layout = QFormLayout(self)

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(3000)  # Проверять каждые 3 секунды
        self.status_timer.timeout.connect(self.check_device_status)
        self.status_timer.start()

        # --- Поля выбора даты, устройства, спектров, заметок ---
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())

        self.device_combo = QComboBox()

        self.device_status_icon = QLabel("⏳")  # Пока статус неизвестен
        device_combo_layout = QHBoxLayout()
        device_combo_layout.addWidget(self.device_combo)
        device_combo_layout.addWidget(self.device_status_icon)

        session = SessionLocal()
        self.devices = (
            session.query(DeviceBinding)
            .options(joinedload(DeviceBinding.device))
            .filter_by(user_id=str(user.id))
            .all()
        )
        session.close()

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
        self.save_btn = QPushButton("Создать")
        self.cancel_btn = QPushButton("Отмена")
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addRow(btn_row)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.device_combo.currentIndexChanged.connect(self.update_spectra_list)
        self.device_combo.currentIndexChanged.connect(self.check_device_status)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)

        self.update_spectra_list()

    def update_spectra_list(self):
        """
        Обновить список спектров при смене устройства.
        """
        idx = self.device_combo.currentIndex()
        self.spectra_list.clear()
        if idx < 0 or not self.devices:
            self.spectra = []
            return
        device_binding = self.devices[idx]
        session = SessionLocal()
        device = session.query(Device).options(joinedload(Device.spectra)).get(device_binding.device_id)
        self.spectra = list(device.spectra)
        for s in self.spectra:
            self.spectra_list.addItem(f"{s.wavelength} ({s.rgb_r}, {s.rgb_g}, {s.rgb_b})")
        session.close()

        self.check_device_status()

    def check_device_status(self):
        """
        Проверяет доступность выбранного устройства.
        """
        idx = self.device_combo.currentIndex()
        if idx < 0 or not self.devices:
            self.device_status_icon.setText("❓")
            self.save_btn.setEnabled(False)
            return
        ip = self.devices[idx].ip_address
        try:
            # Пробуем отправить HEAD-запрос (можно заменить на ping, если нужно)
            resp = requests.head(f"http://{ip}:8080/", timeout=1)
            if resp.status_code < 500:
                self.device_status_icon.setText("🟢")
                self.save_btn.setEnabled(True)
            else:
                self.device_status_icon.setText("🔴")
                self.save_btn.setEnabled(False)
        except Exception:
            self.device_status_icon.setText("🔴")
            self.save_btn.setEnabled(False)

    def get_data(self):
        """
        Получить введённые данные сеанса
        """
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
        self.status_timer.stop()
        super().closeEvent(event)
