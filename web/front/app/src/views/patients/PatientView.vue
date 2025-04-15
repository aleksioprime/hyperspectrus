<template>
  <div>
    <h1 class="text-h5 mb-4">Пациенты</h1>

    <v-snackbar v-model="snackbar.show" :timeout="4000" color="red" variant="tonal">
      {{ snackbar.text }}
    </v-snackbar>

    <v-btn color="primary" class="mb-4" @click="openCreateDialog">
      <v-icon start>mdi-plus</v-icon>
      Добавить
    </v-btn>

    <v-list>
      <v-list-item v-for="(patient, index) in patients" :key="patient.id" link
        @click="goToPatient(patient.id)">
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
            <v-btn icon @click="openEditDialog(patient)" class="me-2">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon @click="deletePatient(patient.id)">
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

    <!-- Модальное окно добавления/редкатирования -->
    <v-dialog v-model="dialog.visible" max-width="500px">
      <v-card>
        <v-card-title>
          {{ dialog.editing ? 'Редактировать пациента' : 'Новый пациент' }}
        </v-card-title>

        <v-card-text>
          <PatientForm v-model="dialog.form" @submit="submitDialog" />
        </v-card-text>

        <v-card-actions class="justify-end">
          <v-btn @click="dialog.visible = false">Отмена</v-btn>
          <v-btn color="primary" @click="submitDialog">
            {{ dialog.editing ? 'Сохранить' : 'Создать' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Модальное окно удаления -->
    <v-dialog v-model="confirmDelete.visible" max-width="400px">
      <v-card>
        <v-card-title>Удалить пациента?</v-card-title>
        <v-card-text>
          Вы уверены, что хотите удалить пациента <strong>{{ confirmDelete.patient?.full_name }}</strong>?
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="confirmDelete.visible = false">Отмена</v-btn>
          <v-btn color="red" @click="confirmDeletePatient">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { onMounted, ref, computed } from "vue";
import { useIntersectionObserver } from "@vueuse/core";
import { format } from "date-fns";
import ru from "date-fns/locale/ru";
import defaultPhoto from '@/assets/img/user-default.png'

import PatientForm from "@/components/patients/PatientForm.vue";

import { usePatientStore } from "@/stores/patient";
const patientStore = usePatientStore();

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();

import { useRouter } from "vue-router";
const router = useRouter();

const goToPatient = (id) => {
  router.push({ name: 'patient-detail', params: { id } });
};

const organizationId = computed(() => authStore.user?.organization_id);

const canEdit = (patient) => {
  return (
    authStore.isAdmin ||
    (organizationId.value && patient.organization_id === organizationId.value)
  );
};

const snackbar = ref({
  show: false,
  text: "",
});

const dialog = ref({
  visible: false,
  editing: false,
  form: {
    id: null,
    full_name: "",
    birth_date: "",
    notes: "",
  },
});

const openCreateDialog = () => {
  if (!organizationId.value) {
    snackbar.value = {
      show: true,
      text: "Вы не можете создавать пациентов, так как не указана организация.",
    };
    return;
  }

  dialog.value = {
    visible: true,
    editing: false,
    form: {
      id: null,
      full_name: "",
      birth_date: "",
      notes: "",
    },
  };
};

const openEditDialog = (patient) => {
  dialog.value = {
    visible: true,
    editing: true,
    form: {
      id: patient.id,
      full_name: patient.full_name,
      birth_date: patient.birth_date,
      notes: patient.notes,
    },
  };
};

const submitDialog = async () => {
  const { form, editing } = dialog.value;

  if (!form.full_name || !form.birth_date) return;

  if (editing) {
    await patientStore.updatePatient(form.id, form);
    const index = patients.value.findIndex(p => p.id === form.id);
    if (index !== -1) patients.value[index] = { ...patients.value[index], ...form };
  } else {
    const newPatient = await patientStore.createPatient({
      ...form,
      organization_id: organizationId.value,
    });
    if (newPatient) patients.value.unshift(newPatient);
  }

  dialog.value.visible = false;
};

const confirmDelete = ref({
  visible: false,
  patient: null,
});

const deletePatient = (id) => {
  const patient = patients.value.find(p => p.id === id);
  confirmDelete.value = {
    visible: true,
    patient,
  };
};

const confirmDeletePatient = async () => {
  const patient = confirmDelete.value.patient;
  const success = await patientStore.deletePatient(patient.id);
  if (success) {
    patients.value = patients.value.filter((p) => p.id !== patient.id);
    confirmDelete.value.visible = false;
  }
};


const patients = ref([]);
const page = ref(0);
const limit = 20;
const total = ref(0);
const loading = ref(false);
const hasNextPage = ref(true);

const infiniteScrollTarget = ref(null);

const fetchPatients = async () => {
  if (loading.value || !hasNextPage.value) return;
  loading.value = true;

  const data = await patientStore.loadPatients({
    offset: page.value,
    limit,
  });

  if (data) {
    patients.value.push(...data.items);
    total.value = data.total;
    hasNextPage.value = data.has_next;
    page.value += 1;
  }

  loading.value = false;
};

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

onMounted(() => {
  fetchPatients();
});

const formatDate = (dateStr) => {
  return format(new Date(dateStr), "d MMMM yyyy", { locale: ru });
};

</script>