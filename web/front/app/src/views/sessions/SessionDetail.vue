<template>
  <div v-if="!session">
    <v-progress-circular indeterminate color="primary" class="ma-4" />
  </div>

  <template v-else>
    <v-breadcrumbs :items="breadcrumbs" class="mb-4 ps-0">
      <template #prepend>
        <v-icon class="me-2">mdi-home</v-icon>
      </template>
    </v-breadcrumbs>

    <h1 class="text-h5 font-weight-bold mb-4">Сеанс от {{ formatDateTime(session.date) }}</h1>

    <v-row>
      <v-col cols="12" sm="6">
        <strong>Устройство:</strong> {{ session.device?.name || session.device_id }}
      </v-col>
      <v-col cols="12" sm="6">
        <strong>Оператор:</strong> {{ session.operator?.first_name }} {{ session.operator?.last_name }}
      </v-col>
      <v-col cols="12" sm="6">
        <strong>Пациент:</strong> {{ session.patient?.full_name }}
      </v-col>
      <v-col cols="12" sm="6">
        <strong>Заметки:</strong>
        <div>{{ session.notes || '—' }}</div>
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <h2 class="text-h6 mb-2">Изображения</h2>
    <v-row>
      <v-col cols="12" md="6">
        <div><strong>Исходные изображения:</strong></div>
        <v-chip v-if="!session.raw_images?.length" color="grey" size="small">нет данных</v-chip>

        <div v-for="img in session.raw_images" :key="img.id" class="mb-2"
          style="position: relative; display: inline-block; min-width: 150px;">
          <!-- Контейнер с относительным позиционированием -->
          <div style="position: relative;">
            <v-img :src="img.file_path" max-height="150" max-width="150" cover class="rounded">
              <template #placeholder>
                <v-skeleton-loader type="image" />
              </template>

              <template #error>
                <div class="d-flex align-center justify-center" style="height: 150px; background-color: #f5f5f5;">
                  <v-icon color="grey" size="48">mdi-image-off</v-icon>
                </div>
              </template>
            </v-img>

            <!-- Кнопка удаления отдельно, поверх изображения -->
            <v-btn icon color="red" size="small" @click="openDeleteDialog(img)" class="position-absolute"
              style="top: 4px; right: 4px; z-index: 2;">
              <v-icon size="18">mdi-delete</v-icon>
            </v-btn>
          </div>
        </div>
        <div>
          <v-btn color="secondary" @click="openUploadDialog">
            <v-icon start>mdi-upload</v-icon>
            Загрузить изображения
          </v-btn>
        </div>
      </v-col>

      <v-col cols="12" md="6">
        <strong>Восстановленные изображения:</strong>
        <v-chip v-if="!session.reconstructed_images?.length" color="grey" size="small">нет данных</v-chip>
        <v-img v-for="img in session.reconstructed_images" :key="img.id" :src="img.file_path" class="mb-2"
          max-height="150" cover />
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <h2 class="text-h6 mb-2">Результат анализа</h2>
    <div v-if="session.result">
      <v-row>
        <v-col cols="12" sm="6">
          <strong>Коэффициент S:</strong> {{ session.result.s_coefficient }}
        </v-col>
        <v-col cols="12" sm="6">
          <strong>THb (поражение):</strong> {{ session.result.mean_lesion_thb }}
        </v-col>
        <v-col cols="12" sm="6">
          <strong>THb (кожа):</strong> {{ session.result.mean_skin_thb }}
        </v-col>
        <v-col cols="12">
          <strong>Контур:</strong>
          <v-img v-if="session.result.contour_path" :src="session.result.contour_path" max-height="150" cover />
          <v-chip v-else color="grey" size="small">нет изображения</v-chip>
        </v-col>
        <v-col cols="12">
          <strong>Заметки:</strong>
          <div>{{ session.result.notes || '—' }}</div>
        </v-col>
      </v-row>
    </div>
    <v-alert v-else type="info">Результаты анализа отсутствуют.</v-alert>

    <v-dialog v-model="uploadDialog.visible" max-width="700px">
      <v-card>
        <v-card-title>Загрузка изображений</v-card-title>
        <v-card-text>
          <RawImageUploadForm ref="formRawImageUploadRef" v-model="uploadDialog.entries" :deviceId="session.device?.id"
            @submit="submitImageUpload" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="uploadDialog.visible = false">Отмена</v-btn>
          <v-btn color="primary" @click="formRawImageUploadRef?.submit()">Загрузить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="confirmDeleteDialog.visible" max-width="400px">
      <v-card>
        <v-card-title class="text-h6">Удаление изображения</v-card-title>
        <v-card-text>Вы уверены, что хотите удалить это изображение?</v-card-text>
        <v-card-actions class="justify-end">
          <v-btn text @click="confirmDeleteDialog.visible = false">Отмена</v-btn>
          <v-btn color="red" @click="deleteImage">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </template>
</template>

<script setup>
import { onMounted, ref, computed } from "vue";
import { format } from "date-fns";
import ru from "date-fns/locale/ru";

// UI & компоненты
import RawImageUploadForm from "@/components/sessions/RawImageUploadForm.vue";

import { useSnackbar } from "@/composables/useSnackbar";
const { showSuccess, snackbar } = useSnackbar();

import { useRoute, useRouter } from "vue-router";
const route = useRoute();
const router = useRouter();

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();

import { useSessionStore } from "@/stores/session";
const sessionStore = useSessionStore();

import { useRawImageStore } from "@/stores/rawImage";
const rawImageStore = useRawImageStore();

const session = ref(null);


const breadcrumbs = computed(() => [
  { title: "Главная", to: { name: "home" }, disabled: false },
  { title: "Пациенты", to: { name: "patient" }, disabled: false },
  { title: session.value?.patient?.full_name || "Загрузка...", to: { name: 'patient-detail', params: { id: session.value?.patient?.id } }, disabled: false },
  { title: `Сеанс от ${formatDateTime(session.value?.date)}`, disabled: true },
]);

onMounted(async () => {
  const patientId = route.params.patient_id || "";
  session.value = await sessionStore.loadSessionDetailed(patientId, route.params.id);
});

const formatDateTime = (dateStr) => {
  return format(new Date(dateStr), "d MMMM yyyy HH:mm", { locale: ru });
};

const uploadDialog = ref({
  visible: false,
  entries: [],
});

const formRawImageUploadRef = ref();

const openUploadDialog = () => {
  uploadDialog.value = {
    visible: true,
    entries: [],
  };
};

const submitImageUpload = async () => {
  const formData = new FormData();

  console.log("Текущие entries:", uploadDialog.value.entries);

  formData.append("session_id", session.value?.id);

  uploadDialog.value.entries.forEach((entry) => {
    formData.append("spectrum_ids", entry.spectrum_id);
    formData.append("files", entry.file);
  });

  console.log("Загружаемые данные: ");
  for (let pair of formData.entries()) {
    console.log(pair[0] + ':', pair[1]);
  }

  const uploaded = await rawImageStore.uploadRawImages(formData);

  if (uploaded) {
    // TODO: обновить список изображений
    showSuccess("Изображения успешно загружены");
    uploadDialog.value.visible = false;
  }
};

const confirmDeleteDialog = ref({
  visible: false,
  image: null,
});

const deleteImage = async () => {
  if (!confirmDeleteDialog.value.image) return;

  await rawImageStore.deleteRawImage(confirmDeleteDialog.value.image.id);

  confirmDeleteDialog.value.visible = false;
  confirmDeleteDialog.value.image = null;

  // Обновление сессии
  const patientId = route.params.patient_id || "";
  session.value = await sessionStore.loadSessionDetailed(patientId, route.params.id);

  showSuccess("Изображение удалено");
};

const openDeleteDialog = (image) => {
  confirmDeleteDialog.value = {
    visible: true,
    image,
  };
};

</script>