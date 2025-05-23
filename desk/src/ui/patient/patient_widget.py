import os
import shutil

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QLabel
)
from sqlalchemy.orm import joinedload

from ui.patient.patient_dialog import PatientDialog
from ui.patient.session_dialog import SessionDialog
from ui.session.session_widget import SessionWidget
from ui.setting.setting_widget import SettingWidget
from ui.patient.device_dialog import DeviceBindingDialog
from services.device_api import create_device_task

from db.db import get_db_session
from db.models import Patient, Session, DeviceBinding


class PatientsWidget(QWidget):
    """
    Виджет для управления пациентами и их сеансами.
    Левый столбец — пациенты, правый — сеансы выбранного пациента.
    """

    def __init__(self, user=None):
        """
        Инициализация PatientsWidget.
        """
        super().__init__()
        self.setWindowTitle("HyperspectRus. Пациенты")
        self.setFixedSize(950, 520)
        self.user = user

        # Главный горизонтальный layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        # ==== ЛЕВАЯ КОЛОНКА: ПАЦИЕНТЫ ====
        left_box = QVBoxLayout()
        # Фильтр по ФИО
        filter_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО...")
        filter_row.addWidget(QLabel("Пациенты"))
        filter_row.addWidget(self.search_edit)
        left_box.addLayout(filter_row)

        # Таблица пациентов
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Дата рождения", "Заметки", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        left_box.addWidget(self.table)

        # Кнопки управления пациентами
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Изменить")
        self.del_btn = QPushButton("Удалить")
        self.settings_btn = QPushButton("Настройки")
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.del_btn)
        btn_row.addWidget(self.settings_btn)
        left_box.addLayout(btn_row)

        # Левая часть — шире
        left_box_widget = QWidget()
        left_box_widget.setLayout(left_box)
        left_box_widget.setMinimumWidth(500)
        main_layout.addWidget(left_box_widget)

        # ==== ПРАВАЯ КОЛОНКА: СЕАНСЫ ====
        right_box = QVBoxLayout()
        self.sessions_label = QLabel("Сеансы пациента:")
        right_box.addWidget(self.sessions_label)

        self.sessions_table = QTableWidget(0, 2)
        self.sessions_table.setHorizontalHeaderLabels(["Дата", "Заметки"])
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.verticalHeader().setVisible(False)
        right_box.addWidget(self.sessions_table)
        self.sessions_table.selectionModel().selectionChanged.connect(self.update_session_buttons_state)

        # Кнопки управления сеансами
        sess_btn_row = QHBoxLayout()
        self.add_session_btn = QPushButton("Создать")
        self.open_session_btn = QPushButton("Открыть")
        self.delete_session_btn = QPushButton("Удалить")
        self.device_ip_btn = QPushButton("Устройства")
        sess_btn_row.addWidget(self.add_session_btn)
        sess_btn_row.addWidget(self.open_session_btn)
        sess_btn_row.addWidget(self.delete_session_btn)
        sess_btn_row.addWidget(self.device_ip_btn)
        right_box.addLayout(sess_btn_row)

        # Правая часть — уже
        right_box_widget = QWidget()
        right_box_widget.setLayout(right_box)
        right_box_widget.setMinimumWidth(300)
        main_layout.addWidget(right_box_widget)

        # ==== ПОДПИСКА НА СОБЫТИЯ ====
        self.add_btn.clicked.connect(self.add_patient)
        self.edit_btn.clicked.connect(self.edit_patient)
        self.del_btn.clicked.connect(self.delete_patient)
        self.settings_btn.clicked.connect(self.open_settings)
        self.search_edit.textChanged.connect(self.filter_table)
        self.table.cellDoubleClicked.connect(self.edit_patient)
        self.table.selectionModel().selectionChanged.connect(self.on_patient_selected)
        self.sessions_table.cellDoubleClicked.connect(self.open_session)
        self.open_session_btn.clicked.connect(self.open_session)
        self.add_session_btn.clicked.connect(self.add_session)
        self.delete_session_btn.clicked.connect(self.delete_session)
        self.device_ip_btn.clicked.connect(self.open_device_bindings)

        # Загрузка данных
        self.reload()
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
            self.on_patient_selected()

    # ===== МЕТОДЫ =====

    def open_settings(self):
        """
        Открывает окно настроек пользователя/системы.
        """
        self.settings_widget = SettingWidget(self)
        self.settings_widget.show()

    def open_device_bindings(self):
        """
        Открывает диалог управления устройствами пользователя и их IP.
        """
        dialog = DeviceBindingDialog(self.user, self)
        dialog.exec()

    # ==== Работа с пациентами ====

    def reload(self):
        """
        Перечитывает список пациентов из БД.
        С учетом организации пользователя, если задано.
        """
        with get_db_session() as session:
            if self.user and self.user.organization_id:
                self.patients = session.query(Patient).filter_by(organization_id=self.user.organization_id).all()
            else:
                self.patients = session.query(Patient).all()
        self.show_patients(self.patients)

    def show_patients(self, patients):
        """
        Заполняет таблицу на основе списка пациентов.

        :param patients: список экземпляров Patient
        """
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for p in patients:
            self.table.insertRow(self.table.rowCount())
            row = self.table.rowCount() - 1
            self.table.setItem(row, 0, QTableWidgetItem(p.full_name))
            bdate_str = p.birth_date.strftime('%d.%m.%Y') if p.birth_date else "—"
            self.table.setItem(row, 1, QTableWidgetItem(bdate_str))
            self.table.setItem(row, 2, QTableWidgetItem(p.notes or ""))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.id)))
        self.table.resizeRowsToContents()
        self.table.setColumnHidden(3, True)  # Скрываем столбец ID
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
        self.table.setSortingEnabled(True)

    def get_selected_patient(self):
        """
        Возвращает выбранного пациента (Patient) или None.
        """
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        id_item = self.table.item(row, 3)
        if not id_item:
            return None
        patient_id = id_item.text()
        with get_db_session() as session:
            patient = session.query(Patient).get(patient_id)
        return patient

    def add_patient(self):
        """
        Открывает диалог создания пациента и добавляет его в базу данных.
        """
        dlg = PatientDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["full_name"]:
                QMessageBox.warning(self, "Ошибка", "ФИО не должно быть пустым!")
                return
            if not data["birth_date"]:
                QMessageBox.warning(self, "Ошибка", "Дата рождения не заполнена!")
                return
            with get_db_session() as session:
                p = Patient(
                    full_name=data["full_name"],
                    birth_date=data["birth_date"],
                    notes=data["notes"],
                    organization_id=self.user.organization_id if self.user else None
                )
                session.add(p)
                session.commit()
            self.reload()

    def edit_patient(self):
        """
        Открывает диалог редактирования пациента, обновляет данные в БД.
        """
        p = self.get_selected_patient()
        if not p:
            QMessageBox.warning(self, "Ошибка", "Выберите пациента для изменения.")
            return
        dlg = PatientDialog(self, patient=p)
        if dlg.exec():
            data = dlg.get_data()
            if not data["full_name"]:
                QMessageBox.warning(self, "Ошибка", "ФИО не должно быть пустым!")
                return
            if not data["birth_date"]:
                QMessageBox.warning(self, "Ошибка", "Дата рождения не заполнена!")
                return
            with get_db_session() as session:
                patient = session.query(Patient).get(p.id)
                patient.full_name = data["full_name"]
                patient.birth_date = data["birth_date"]
                patient.notes = data["notes"]
                session.commit()
            self.reload()

    def delete_patient(self):
        """
        Удаляет выбранного пациента из БД с подтверждением.
        """
        p = self.get_selected_patient()
        if not p:
            QMessageBox.warning(self, "Ошибка", "Выберите пациента для удаления.")
            return
        confirm = QMessageBox.question(
            self, "Подтвердите удаление",
            f"Удалить пациента «{p.full_name}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            with get_db_session() as session:
                patient = session.query(Patient).get(p.id)
                session.delete(patient)
                session.commit()
            self.reload()
            if self.table.rowCount() > 0:
                self.table.selectRow(0)

    def filter_table(self, text):
        """
        Фильтрует пациентов по ФИО (без изменения данных в self.patients).
        """
        filtered = []
        t = text.strip().lower()
        for p in self.patients:
            if t in p.full_name.lower():
                filtered.append(p)
        self.show_patients(filtered)
        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    # ==== Работа с сеансами ====

    def on_patient_selected(self):
        """
        Обновляет таблицу сеансов при выборе пациента.
        """
        patient = self.get_selected_patient()
        if patient:
            self.reload_sessions(patient)
            self.sessions_label.setText(f"Сеансы: {patient.full_name}")
        else:
            self.sessions_table.setRowCount(0)
            self.sessions_label.setText("Сеансы пациента:")

        self.update_session_buttons_state()

    def reload_sessions(self, patient, selected_session_id=None):
        """
        Перечитывает список сеансов из БД для указанного пациента.
        Если передан selected_session_id — выделяет строку с этим сеансом.
        """
        with get_db_session() as session:
            sessions = (
                session.query(Session)
                .filter_by(patient_id=patient.id)
                .order_by(Session.date.desc())
                .all()
            )
        self.sessions_table.setRowCount(0)
        for s in sessions:
            self.sessions_table.insertRow(self.sessions_table.rowCount())
            row = self.sessions_table.rowCount() - 1
            dt_str = s.date.strftime('%d.%m.%Y %H:%M') if s.date else "—"
            self.sessions_table.setItem(row, 0, QTableWidgetItem(dt_str))
            self.sessions_table.setItem(row, 1, QTableWidgetItem(s.notes or ""))

        # --- Выделяем строку по ID, если нужно ---
        selected_row = 0
        if selected_session_id is not None:
            for i, s in enumerate(sessions):
                if s.id == selected_session_id:
                    selected_row = i
                    break
        if self.sessions_table.rowCount() > 0:
            self.sessions_table.selectRow(selected_row)

        self.update_session_buttons_state()

    def get_selected_session(self):
        """
        Возвращает выбранный сеанс (Session) для текущего пациента.
        """
        patient = self.get_selected_patient()
        if not patient:
            return None
        selected = self.sessions_table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        with get_db_session() as session:
            sessions = (
                session.query(Session)
                .options(
                    joinedload(Session.patient),
                    joinedload(Session.device_binding).joinedload(DeviceBinding.device),
                    joinedload(Session.operator),
                    joinedload(Session.result),
                )
                .filter_by(patient_id=patient.id)
                .order_by(Session.date.desc())
                .all()
            )
        if row >= len(sessions):
            return None
        return sessions[row]

    def open_session(self):
        """
        Открывает окно просмотра выбранного сеанса.
        Передаёт в SessionWidget объект сеанса и API-URL устройства.
        """
        s = self.get_selected_session()
        if not s:
            QMessageBox.warning(self, "Ошибка", "Выберите сеанс для открытия.")
            return

        # Создаём и показываем окно SessionWidget
        self.session_widget = SessionWidget(session=s)
        self.session_widget.show()

    def add_session(self):
        """
        Открывает диалог создания сеанса, отправляет задачу на устройство,
        а затем добавляет сеанс в базу данных.
        """
        patient = self.get_selected_patient()
        if not patient:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите пациента.")
            return

        dlg = SessionDialog(self.user, self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["date"]:
                QMessageBox.warning(self, "Ошибка", "Дата сеанса не указана!")
                return
            if not data["device_binding"]:
                QMessageBox.warning(self, "Ошибка", "Не выбрано устройство!")
                return
            if not data["spectra"]:
                QMessageBox.warning(self, "Ошибка", "Не выбраны спектры!")
                return

            spectra = [
                {
                    "id": str(s.id),
                    "rgb": [c if c is not None else 0 for c in (s.rgb_r, s.rgb_g, s.rgb_b)]
                }
                for s in data["spectra"]
            ]
            try:
                # Получаем результат создания задачи на устройстве
                task_info = create_device_task(
                    ip_address=data["device_binding"].ip_address,
                    title=f"Сеанс {patient.full_name} {data['date'].strftime('%d.%m.%Y')}",
                    spectra=spectra
                )
                task_id = task_info.get("id")
                if not task_id:
                    raise Exception("Не удалось получить id задачи устройства")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось отправить задание на устройство:\n{e}")
                return

            with get_db_session() as session:
                new_session = Session(
                    patient_id=patient.id,
                    date=data["date"],
                    notes=data["notes"] or "",
                    device_binding_id=data["device_binding"].id,
                    operator_id=self.user.id,
                    device_task_id=task_id,
                )
                session.add(new_session)
                session.commit()
                new_session_id = new_session.id

            self.reload_sessions(patient, selected_session_id=new_session_id)

            self.open_session()

    def remove_session_dir_if_exists(self, session):
        """
        Удаляет папку session_xxx для этого сеанса вместе со всем содержимым.
        Находит путь к папке по любому связанному файлу (raw, reconstructed, result).
        """
        all_files = []
        for img in session.raw_images:
            if img.file_path:
                all_files.append(img.file_path)
        for img in session.reconstructed_images:
            if img.file_path:
                all_files.append(img.file_path)
        if session.result:
            if session.result.contour_path:
                all_files.append(session.result.contour_path)
            if session.result.thb_path:
                all_files.append(session.result.thb_path)

        # Находим первую реально существующую папку session_xxx
        for f in all_files:
            if f and os.path.exists(f):
                session_dir = os.path.dirname(f)
                # Дополнительно убедимся, что это именно session_xxx
                if os.path.basename(session_dir).startswith("session_") and os.path.isdir(session_dir):
                    try:
                        shutil.rmtree(session_dir)
                    except Exception as e:
                        print(f"Ошибка при удалении папки {session_dir}: {e}")
                    break

    def delete_session(self):
        """
        Удаляет выбранный сеанс после подтверждения пользователя.
        Также удаляет все связанные фото (raw/reconstructed) и результат.
        """
        patient = self.get_selected_patient()
        if not patient:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите пациента.")
            return

        s = self.get_selected_session()
        if not s:
            QMessageBox.warning(self, "Ошибка", "Выберите сеанс для удаления.")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить сеанс от {s.date.strftime('%d.%m.%Y %H:%M')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            with get_db_session() as session:
                # Загрузим сеанс с подгруженными фотографиями и результатами
                sess = session.query(Session)\
                    .options(
                        joinedload(Session.raw_images),
                        joinedload(Session.reconstructed_images),
                        joinedload(Session.result)
                    ).get(s.id)

                self.remove_session_dir_if_exists(sess)

                # Удаляем сам сеанс (удалит все raw/reconstructed images по cascade)
                session.delete(sess)
                session.commit()

            self.reload_sessions(patient)
            if self.sessions_table.rowCount() > 0:
                self.sessions_table.selectRow(0)

    def update_session_buttons_state(self):
        """
        Включает или выключает кнопки "Открыть" и "Удалить сеанс"
        в зависимости от того, выбран ли сеанс.
        """
        enabled = self.sessions_table.selectionModel().hasSelection() and self.sessions_table.rowCount() > 0
        self.open_session_btn.setEnabled(enabled)
        self.delete_session_btn.setEnabled(enabled)
