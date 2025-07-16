<template>
  <div>
    <h1 class="text-h5 mb-4">Пациенты</h1>

    <div class="d-flex align-top justify-space-between">
      <v-btn v-if="canEdit" color="primary" class="my-2" @click="openEditDialog()">
        <v-icon start>mdi-plus</v-icon>
        Добавить
      </v-btn>
      <v-select v-if="authStore.isSuperuser" v-model="selectedOrganization" :items="organizations" item-value="id" item-title="name"
        label="Организация" clearable style="max-width: 300px" />
    </div>

    <v-list class="pa-0 mt-4">
      <v-list-item v-for="(patient, index) in patients" :key="patient.id" link @click="goToPatient(patient.id)">
        <!-- Фото (если есть) -->
        <template #prepend>
          <v-avatar size="56">
            <v-img :src="patient.photo || defaultPhoto" alt="Фото пациента" cover />
          </v-avatar>
        </template>

        <!-- Контент -->
        <v-list-item-title>{{ patient.full_name }}</v-list-item-title>
        <v-list-item-subtitle>
          Дата рождения: {{ formatDate(patient.birth_date) }}
        </v-list-item-subtitle>
        <v-list-item-subtitle v-if="patient.notes">
          Заметки: {{ patient.notes }}
        </v-list-item-subtitle>

        <!-- Например, кнопки редактирования или удаления -->
        <template #append>
          <template v-if="canEdit(patient)">
            <v-btn icon @click.stop="openEditDialog(patient)" class="me-2">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon @click.stop="deletePatient(patient)">
              <v-icon color="red">mdi-delete</v-icon>
            </v-btn>
          </template>
        </template>
      </v-list-item>
    </v-list>

    <div ref="infiniteScrollTarget" />

    <div class="text-center my-4" v-if="loading">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <div class="text-center my-4" v-if="!loading && !hasNextPage && patients.length">
      <v-alert type="info" density="compact" border="start" variant="tonal">
        Все пациенты загружены
      </v-alert>
    </div>

    <v-alert v-if="!patients.length" type="info" class="mt-4">
      Пациенты пока не добавлены
    </v-alert>

    <!-- Модальное окно добавления/редактирования -->
    <v-dialog v-model="modalDialogEdit.visible" max-width="500px" persistent>
      <v-card>
        <v-card-title>
          {{ modalDialogEdit.editing ? 'Редактировать пациента' : 'Новый пациент' }}
        </v-card-title>
        <v-card-text>
          <PatientForm ref="patientFormRef" v-model="modalDialogEdit.form" @submit="submitDialog" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="modalDialogEdit.visible = false">Отмена</v-btn>
          <v-btn color="primary" @click="submitDialog">
            {{ modalDialogEdit.editing ? 'Сохранить' : 'Создать' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Модальное окно удаления -->
    <v-dialog v-model="modalDialogDelete.visible" max-width="400px">
      <v-card>
        <v-card-title>Удалить пациента?</v-card-title>
        <v-card-text>
          Вы уверены, что хотите удалить пациента <strong>{{ modalDialogDelete.patient?.full_name }}</strong>?
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="modalDialogDelete.visible = false">Отмена</v-btn>
          <v-btn color="red" @click="confirmDeletePatient">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useIntersectionObserver } from "@vueuse/core";
import { format } from "date-fns";
import ru from "date-fns/locale/ru";

import defaultPhoto from '@/assets/img/user-default.png'
import PatientForm from "@/components/patients/PatientForm.vue";

import { usePatientStore } from "@/stores/patient";
const patientStore = usePatientStore();
const patients = ref([]);

import { useOrganizationStore } from "@/stores/organization";
const organizationStore = useOrganizationStore();
const organizations = ref([]);

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();

import { useRouter } from "vue-router";
const router = useRouter();

const goToPatient = (id) => {
  router.push({ name: 'patient-detail', params: { id } });
};

const organizationId = computed(() => authStore.user?.organization?.id);

const canEdit = (patient) => {
  return (
    authStore.isAdmin ||
    authStore.isSuperuser ||
    (organizationId.value && patient.organization?.id === organizationId.value)
  );
};

const snackbar = ref({
  show: false,
  text: "",
});

// --- СПИСОК ПАЦИЕНТОВ ---

// Переменные пагинированного списка
const page = ref(1);
const limit = 20;
const total = ref(0);
const hasNextPage = ref(true);

// Переменная процесса загрузки
const loading = ref(false);

// Загрузка пагинированного списка
const fetchPatients = async (reset = false) => {
  if (loading.value) return;
  loading.value = true;

  // Если изменился фильтр или нужно перезагрузить весь список:
  if (reset) {
    patients.value = [];
    page.value = 1;
    hasNextPage.value = true;
  }

  // Формируем параметры запроса для API
  const params = {
    offset: page.value,
    limit,
  };

  // Добавление фильтров в параметры
  if (selectedOrganization.value) {
    params.organization_id = selectedOrganization.value;
  }

  // Запрос к API с передачей параметров
  const data = await patientStore.loadPatients({ params: params });

  // Если данные получены
  if (data) {
    patients.value.push(...data.items);
    total.value = data.total;
    hasNextPage.value = data.has_next;
    page.value += 1;
  }

  loading.value = false;
};

// Элемент страницы, который активирует подзагрузку списка
const infiniteScrollTarget = ref(null);

// Хук, который следит, попал ли элемент подзагрузки списка в поле видимости
useIntersectionObserver(
  infiniteScrollTarget,
  ([{ isIntersecting }]) => {
    if (isIntersecting) {
      fetchPatients();
    }
  },
  {
    threshold: 1.0,
  }
);

// --- ФИЛЬТР ПО ОРГАНИЗАЦИИ ---
const selectedOrganization = ref(null);

onMounted(async () => {
  if (authStore.isSuperuser) {
    organizations.value = await organizationStore.loadOrganizations?.() || [];
  }
});

watch(selectedOrganization, () => {
  fetchPatients(true);
});

// --- ДОБАВЛЕНИЕ/РЕДАКТИРОВАНИЕ ПАЦИЕНТОВ ---

// Объект модального окна
const modalDialogEdit = ref({
  visible: false,
  editing: false,
  form: {},
});

// Открытие модального окна для создания/редактирования пациента
const openEditDialog = (patient = null) => {

  if (!organizationId.value) {
    snackbar.value = {
      show: true,
      text: "Вы не можете создавать пациентов, так как не указана организация.",
    };
    return;
  }

  modalDialogEdit.value = {
    visible: true,
    editing: !!patient,
    form: patient
      ? { ...patient }
      : {
        id: null,
        full_name: "",
        birth_date: "",
        notes: "",
        organization_id: organizationId.value
      }
  };
};

// Подготовка данных формы для запроса создания/редактирования пациентов
const getFormPayload = (form) => ({ ...form });

// Подтверждение создания/редактирования пациента
const patientFormRef = ref();

const submitDialog = async () => {
  const valid = await patientFormRef.value?.submit();
  if (!valid) return;

  const { form, editing } = modalDialogEdit.value;

  if (editing) {
    const result = await patientStore.updatePatient(form.id, getFormPayload(form));
    if (!result) return;

    const index = patients.value.findIndex(p => p.id === form.id);
    if (index !== -1) patients.value[index] = { ...patients.value[index], ...form };

  } else {
    const newPatient = await patientStore.createPatient(getFormPayload(form));
    if (!newPatient) return;

    await fetchPatients(true);
  }

  modalDialogEdit.value.visible = false;
};

// --- УДАЛЕНИЕ ПАЦИЕНТА ---

// Объект модального окна
const modalDialogDelete = ref({
  visible: false,
  patient: null,
});

// Вызов модального окна удаления
const deletePatient = (patient) => {
  modalDialogDelete.value = {
    visible: true,
    patient,
  };
};

// Подтверждение удаления в модальном окне
const confirmDeletePatient = async () => {
  const patient = modalDialogDelete.value.patient;

  const result = await patientStore.deletePatient(patient.id);
  if (!result) return;

  patients.value = patients.value.filter((p) => p.id !== patient.id);
  modalDialogDelete.value.visible = false;
};



const formatDate = (dateStr) => {
  return format(new Date(dateStr), "d MMMM yyyy", { locale: ru });
};

</script>