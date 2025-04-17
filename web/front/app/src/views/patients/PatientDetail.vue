<template>
  <!-- Назад -->
  <!-- <v-btn variant="text" @click="router.back()" class="mb-2">
    <v-icon start>mdi-arrow-left</v-icon>
    Назад
  </v-btn> -->

  <v-breadcrumbs :items="breadcrumbs" class="mb-4 ps-0">
    <template #prepend>
      <v-icon class="me-2">mdi-home</v-icon>
    </template>
  </v-breadcrumbs>

  <template v-if="!patient">
    <v-progress-circular indeterminate color="primary" class="ma-4" />
  </template>

  <!-- Только если пациент загружен -->
  <template v-if="patient">
    <h1 class="text-h5 font-weight-bold mb-2">Пациент: {{ patient?.full_name }}</h1>

    <v-row class="mb-4">
      <v-col cols="12" sm="6">
        <strong>Дата рождения:</strong> {{ formatDate(patient.birth_date) }}
      </v-col>
      <v-col cols="12" sm="6">
        <strong>Заметки:</strong> {{ patient.notes || '—' }}
      </v-col>
    </v-row>

    <v-divider class="my-4" />


    <div class="d-flex justify-space-between align-center mb-2">
      <h2 class="text-h6">Сеансы</h2>
      <v-btn color="primary" @click="addSession">
        <v-icon start>mdi-plus</v-icon>
        Добавить сеанс
      </v-btn>
    </div>

    <v-table dense>
      <thead>
        <tr>
          <th>Дата</th>
          <th>Оператор</th>
          <th>Заметки</th>
          <th class="text-end">Действия</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="session in patient.sessions" :key="session.id">
          <td>
            <v-icon size="18" color="primary" class="me-1">mdi-calendar</v-icon>
            {{ formatDateTime(session.date) }}
          </td>
          <td>
            <v-icon size="18" color="info" class="me-1">mdi-account</v-icon>
            <span v-if="session.operator_id === currentUser?.id">
              {{ currentUser.first_name }} {{ currentUser.last_name }}
            </span>
            <span v-else>
              {{ session.operator_id }}
            </span>
          </td>
          <td>{{ session.notes || '—' }}</td>
          <td class="text-end">
            <v-btn icon size="small" @click="openSession(session.id)" :title="'Открыть сеанс'">
              <v-icon color="primary">mdi-eye</v-icon>
            </v-btn>
            <v-btn icon size="small" @click="editSession(session)" :title="'Редактировать сеанс'">
              <v-icon color="orange">mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon size="small" @click="deleteSession(session.id)" :title="'Удалить сеанс'">
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

  <!-- Модалка создания/редактирования -->
  <v-dialog v-model="sessionDialog.visible" max-width="500px">
    <v-card>
      <v-card-title>
        {{ sessionDialog.editing ? "Редактировать сеанс" : "Новый сеанс" }}
      </v-card-title>
      <v-card-text>
        <SessionForm ref="formSessionRef" v-model="sessionDialog.form" @submit="submitSessionDialog" />
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="sessionDialog.visible = false">Отмена</v-btn>
        <v-btn color="primary" @click="formSessionRef?.submit()">
          {{ sessionDialog.editing ? "Сохранить" : "Создать" }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Модалка подтверждения удаления -->
  <v-dialog v-model="confirmDelete.visible" max-width="400px">
    <v-card>
      <v-card-title>Удалить сеанс?</v-card-title>
      <v-card-text>
        Вы уверены, что хотите удалить этот сеанс?
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="confirmDelete.visible = false">Отмена</v-btn>
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
import { useRoute, useRouter } from "vue-router";
import { format } from "date-fns";
import ru from "date-fns/locale/ru";

// Сторы
import { usePatientStore } from "@/stores/patient";
import { useAuthStore } from "@/stores/auth";
import { useSessionStore } from "@/stores/session";

// UI & компоненты
import SessionForm from "@/components/sessions/SessionForm.vue";
import { useSnackbar } from "@/composables/useSnackbar";

// --- Инициализация ---
const route = useRoute();
const router = useRouter();
const patientStore = usePatientStore();
const sessionStore = useSessionStore();
const authStore = useAuthStore();
const currentUser = computed(() => authStore.user);
const { showSuccess, snackbar } = useSnackbar();

// Пациент
const patient = ref(null);

// Breadcrumbs
const breadcrumbs = computed(() => [
  { title: "Главная", to: { name: "home" }, disabled: false },
  { title: "Пациенты", to: { name: "patient" }, disabled: false },
  { title: patient.value?.full_name || "Загрузка...", disabled: true },
]);

// Загрузка пациента
onMounted(async () => {
  patient.value = await patientStore.loadPatientDetailed(route.params.id);
});

// --- Форматирование дат ---
const formatDate = (dateStr) => format(new Date(dateStr), "d MMMM yyyy", { locale: ru });
const formatDateTime = (dateStr) => format(new Date(dateStr), "d MMMM yyyy HH:mm", { locale: ru });

// --- Управление формой сеанса ---
const formSessionRef = ref();

const sessionDialog = ref({
  visible: false,
  editing: false,
  form: {
    id: null,
    device_id: null,
    date: "",
    operator_id: "",
    notes: "",
  },
});

// Открыть форму добавления
const addSession = () => {
  sessionDialog.value = {
    visible: true,
    editing: false,
    form: {
      id: null,
      device_id: null,
      date: new Date().toISOString().slice(0, 16),
      operator_id: currentUser.value?.id,
      notes: "",
    },
  };
};

// Открыть форму редактирования
const editSession = (session) => {
  sessionDialog.value = {
    visible: true,
    editing: true,
    form: {
      id: session.id,
      device_id: session.device_id,
      date: session.date.slice(0, 16),
      operator_id: session.operator_id,
      notes: session.notes || "",
    },
  };
};

// Обработка отправки формы
const submitSessionDialog = async () => {
  const form = sessionDialog.value.form;

  if (!form.date || !form.operator_id || !form.device_id) return;

  if (sessionDialog.value.editing) {
    const updated = await sessionStore.updateSession(patient.value.id, form.id, form);
    if (updated) {
      const index = patient.value.sessions.findIndex(s => s.id === form.id);
      if (index !== -1) patient.value.sessions[index] = { ...patient.value.sessions[index], ...updated };
      showSuccess("Сеанс обновлён");
    }
  } else {
    const newSession = await sessionStore.createSession(patient.value.id, form);
    if (newSession) {
      patient.value.sessions.unshift(newSession);
      showSuccess("Сеанс добавлен");
    }
  }

  sessionDialog.value.visible = false;
};

// --- Удаление сеанса ---
const confirmDelete = ref({ visible: false, sessionId: null });

const deleteSession = (id) => {
  confirmDelete.value = {
    visible: true,
    sessionId: id,
  };
};

const confirmDeleteSession = async () => {
  const sessionId = confirmDelete.value.sessionId;
  const patientId = patient.value.id;

  const success = await sessionStore.deleteSession(patientId, sessionId);
  if (success) {
    patient.value.sessions = patient.value.sessions.filter(s => s.id !== sessionId);
    showSuccess("Сеанс успешно удалён");
  }

  confirmDelete.value.visible = false;
};

// --- Переход на детальную страницу сеанса ---
const openSession = (sessionId) => {
  router.push({ name: "session-detail", params: { patient_id: patient.value.id, id: sessionId } });
};
</script>
