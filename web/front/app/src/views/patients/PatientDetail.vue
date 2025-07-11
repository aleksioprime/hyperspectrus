<template>
  <!-- Анимация загрузки пациента -->
  <div v-if="!patient" class="d-flex align-center justify-center mt-6">
    <v-progress-circular indeterminate color="primary" class="ma-4" />
  </div>

  <!-- Информация о пациенте -->
  <template v-if="patient">
    <v-breadcrumbs :items="breadcrumbs" class="mb-4 ps-0">
      <template #prepend>
        <v-icon class="me-2">mdi-home</v-icon>
      </template>
    </v-breadcrumbs>

    <h1 class="text-h5 font-weight-bold mb-2">Пациент: {{ patient?.full_name }}</h1>

    <div class="mb-4">
      <v-row>
        <v-col cols="12" sm="4">
          <strong>Дата рождения:</strong> {{ formatDate(patient.birth_date) }}
        </v-col>
        <v-col cols="12" sm="8">
          <strong>Заметки:</strong> {{ patient.notes || '—' }}
        </v-col>
      </v-row>
      <div class="mt-2">
        <strong>Организация приёма:</strong> {{ patient.organization?.name || '—' }}
      </div>
    </div>

    <v-divider class="my-4" />

    <!-- Работа с сеансами -->

    <div class="d-flex justify-space-between align-center mb-2">
      <h2 class="text-h6">Сеансы</h2>
      <v-btn color="primary" @click="openEditDialog()">
        <v-icon start>mdi-plus</v-icon>
        Добавить сеанс
      </v-btn>
    </div>

    <v-table dense>
      <thead>
        <tr>
          <th style="width: 120px;"><v-icon size="18" color="primary" class="me-1">mdi-calendar</v-icon>Дата</th>
          <th style="width: 200px;"><v-icon size="18" color="info" class="me-1">mdi-account</v-icon>Оператор</th>
          <th style="width: 200px;"><v-icon size="18" color="info" class="me-1">mdi-account</v-icon>Устройство</th>
          <th>Заметки</th>
          <th style="width: 130px;"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="session in patient.sessions" :key="session.id" @click="openSession(session.id)"
          class="hoverable-row">
          <td>
            {{ formatDateTime(session.date) }}
          </td>
          <td>
              {{ session.operator?.first_name }} {{ session.operator?.last_name }}
          </td>
          <td>
              {{ session.device?.name }}
          </td>
          <td>{{ session.notes || '—' }}</td>
          <td>
            <v-btn icon size="small" class="ms-2" @click.stop="openEditDialog(session)" :title="'Редактировать сеанс'">
              <v-icon color="orange">mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon size="small" class="ms-2" @click.stop="deleteSession(session)" :title="'Удалить сеанс'">
              <v-icon color="red">mdi-delete</v-icon>
            </v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>

    <v-alert v-if="!patient.sessions.length" type="info" class="mt-4">
      У пациента пока нет сеансов.
    </v-alert>
  </template>

  <!-- Модальное окно создания/редактирования -->
  <v-dialog v-model="modalDialogEdit.visible" max-width="500px">
    <v-card>
      <v-card-title>
        {{ modalDialogEdit.editing ? "Редактировать сеанс" : "Новый сеанс" }}
      </v-card-title>
      <v-card-text>
        <SessionForm ref="sessionFormRef" v-model="modalDialogEdit.form" :is-create="!modalDialogEdit.editing"/>
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="modalDialogEdit.visible = false">Отмена</v-btn>
        <v-btn color="primary" @click="submitDialog">
          {{ modalDialogEdit.editing ? "Сохранить" : "Создать" }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Модальное окно подтверждения удаления -->
  <v-dialog v-model="modalDialogDelete.visible" max-width="400px">
    <v-card>
      <v-card-title>Удалить сеанс?</v-card-title>
      <v-card-text>
        Вы уверены, что хотите удалить этот сеанс?
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="modalDialogDelete.visible = false">Отмена</v-btn>
        <v-btn color="red" @click="confirmDeleteSession">Удалить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="snackbar.timeout">
    {{ snackbar.text }}
  </v-snackbar>

</template>

<script setup>
import { onMounted, ref, computed } from "vue";
import { format } from "date-fns";
import ru from "date-fns/locale/ru";

import SessionForm from "@/components/sessions/SessionForm.vue";
import { useSnackbar } from "@/composables/useSnackbar";
const { showSuccess, snackbar } = useSnackbar();

import { usePatientStore } from "@/stores/patient";
const patientStore = usePatientStore();

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();
const currentUser = computed(() => authStore.user);

import { useSessionStore } from "@/stores/session";
const sessionStore = useSessionStore();

import { useRoute, useRouter } from "vue-router";
const route = useRoute();
const router = useRouter();

const breadcrumbs = computed(() => [
  { title: "Пациенты", to: { name: "patient" }, disabled: false },
  { title: patient.value?.full_name || "Загрузка...", disabled: true },
]);

// Текущий пациент
const patient = ref(null);

onMounted(async () => {
  patient.value = await patientStore.loadPatientDetailed(route.params.id);
});

// Переход на детальную страницу сеанса
const openSession = (sessionId) => {
  router.push({ name: "session-detail", params: { patient_id: patient.value.id, id: sessionId } });
};

// Форматирование дат
const formatDate = (dateStr) => format(new Date(dateStr), "d MMMM yyyy", { locale: ru });
const formatDateTime = (dateStr) => format(new Date(dateStr), "d MMMM yyyy HH:mm", { locale: ru });

// --- ДОБАВЛЕНИЕ/РЕДАКТИРОВАНИЕ СЕАНСОВ ---

// Объект модального окна
const modalDialogEdit = ref({
  visible: false,
  editing: false,
  form: {},
});

// Открытие модального окна для создания/редактирования сеанса
const openEditDialog = (session = null) => {
  modalDialogEdit.value = {
    visible: true,
    editing: !!session,
    form: session
      ? {
        ...session,
        device_id: session.device.id,
        date: session.date.slice(0, 16),
      }
      : {
        id: null,
        device_id: null,
        date: new Date().toISOString().slice(0, 16),
        operator_id: currentUser.value?.id,
        notes: "",
      },
  };
};

// Подготовка данных формы для запроса создания/редактирования сеансов
const getFormPayload = (form) => ({ ...form });

// Подтверждение создания/редактирования пациента
const sessionFormRef = ref();

// Обработка отправки формы
const submitDialog = async () => {
  const valid = await sessionFormRef.value?.submit();
  if (!valid) return;

  const { form, editing } = modalDialogEdit.value;

  if (editing) {
    const result = await sessionStore.updateSession(patient.value.id, form.id, getFormPayload(form));
    if (!result) return;

    const index = patient.value.sessions.findIndex(s => s.id === form.id);
    if (index !== -1) patient.value.sessions[index] = { ...patient.value.sessions[index], ...form };

  } else {
    const newSession = await sessionStore.createSession(patient.value.id, form);
    if (!newSession) return

    patient.value.sessions.unshift(newSession);
  }

  modalDialogEdit.value.visible = false;
};

// --- УДАЛЕНИЕ CЕАНСА ---

// Объект модального окна
const modalDialogDelete = ref({
  visible: false,
  session: null,
});

// Вызов модального окна удаления
const deleteSession = (session) => {
  modalDialogDelete.value = {
    visible: true,
    session,
  };
};

const confirmDeleteSession = async () => {
  const session = modalDialogDelete.value.session;

  const result = await sessionStore.deleteSession(patient.value?.id, session.id);
  if (!result) return;

  patient.value.sessions = patient.value.sessions.filter(s => s.id !== session.id);
  modalDialogDelete.value.visible = false;
};

</script>

<style scoped>
.hoverable-row:hover {
  background: #f0f0f7;
  cursor: pointer;
}
</style>