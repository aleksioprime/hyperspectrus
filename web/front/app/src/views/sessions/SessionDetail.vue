<template>
  <!-- Анимация загрузки сеанса -->
  <div v-if="!session" class="d-flex align-center justify-center mt-6">
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
        <div class="my-2">
          <strong>Устройство:</strong> {{ session.device?.name || session.device_id }}
        </div>
        <div class="my-2">
          <strong>Оператор:</strong> {{ session.operator?.first_name }} {{ session.operator?.last_name }}
        </div>
        <div class="my-2">
          <strong>Пациент:</strong> {{ session.patient?.full_name }}
        </div>
      </v-col>
      <v-col cols="12" sm="6">
        <div class="my-2">
          <strong>Заметки:</strong>
          <div>{{ session.notes || '—' }}</div>
        </div>
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <h2 class="text-h6 mb-2">Изображения</h2>
    <v-row>
      <!-- Блок исходных изображений -->
      <v-col cols="12" md="6">
        <div><strong>Исходные изображения:</strong></div>
        <div>
          <v-chip v-if="!session.raw_images?.length" color="grey" size="small" class="my-2">нет данных</v-chip>
        </div>

        <div class="d-flex flex-wrap gap-4">
          <div v-for="img in session.raw_images" :key="img.id"
            style="width: 150px; position: relative; text-align: center;" class="pa-1">
            <div style="position: relative;">
              <!-- Изображение с фиксированным размером -->
              <v-img :src="img.file_path" width="150" height="150" cover class="rounded">
                <template #placeholder>
                  <v-skeleton-loader type="image" />
                </template>
                <template #error>
                  <div class="d-flex align-center justify-center" style="height: 150px; background-color: #f5f5f5;">
                    <v-icon color="grey" size="48">mdi-image-off</v-icon>
                  </div>
                </template>
              </v-img>
              <!-- Кнопка удаления -->
              <v-btn icon color="red" size="small" @click="openDeleteDialog(img)" class="position-absolute"
                style="top: 4px; right: 4px; z-index: 2;">
                <v-icon size="18">mdi-delete</v-icon>
              </v-btn>
            </div>
            <!-- Подпись под изображением -->
            <div class="mt-1" style="font-size: 14px; color: #888;">
              {{ img.spectrum?.wavelength ? img.spectrum.wavelength + ' нм' : '—' }}
            </div>
          </div>
        </div>

        <div>
          <v-btn v-if="session.raw_images.length" color="warning" @click="openDeleteManyDialog">
            <v-icon start>mdi-delete</v-icon>
            Удалить
          </v-btn>
          <v-btn v-else color="secondary" @click="openUploadDialog">
            <v-icon start>mdi-upload</v-icon>
            Загрузить
          </v-btn>
        </div>
      </v-col>

      <!-- Блок обработанных изображений -->
      <v-col cols="12" md="6">
        <strong>Восстановленные изображения:</strong>
        <div>
          <v-chip v-if="!session.reconstructed_images?.length" color="grey" size="small" class="my-2">нет
            данных</v-chip>
        </div>

        <div class="d-flex flex-wrap gap-4">
          <div v-for="img in session.reconstructed_images" :key="img.id"
            style="width: 150px; position: relative; text-align: center;" class="pa-1">
            <div style="position: relative;">
              <!-- Изображение с фиксированным размером -->
              <v-img :src="img.file_path" width="150" height="150" cover class="rounded">
                <template #placeholder>
                  <v-skeleton-loader type="image" />
                </template>
                <template #error>
                  <div class="d-flex align-center justify-center" style="height: 150px; background-color: #f5f5f5;">
                    <v-icon color="grey" size="48">mdi-image-off</v-icon>
                  </div>
                </template>
              </v-img>
              <!-- Кнопка удаления -->
              <v-btn icon color="red" size="small" @click="openDeleteDialog(img)" class="position-absolute"
                style="top: 4px; right: 4px; z-index: 2;">
                <v-icon size="18">mdi-delete</v-icon>
              </v-btn>
            </div>
            <!-- Подпись под изображением -->
            <div class="mt-1" style="font-size: 14px; color: #888;">
              {{ img.chromophore?.symbol ? img.chromophore.symbol : '—' }}
            </div>
          </div>
        </div>

      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <!-- Блок результатов анализа  -->
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
          <strong>Заметки:</strong>
          <div>{{ session.result.notes || '—' }}</div>
        </v-col>
      </v-row>
    </div>
    <v-alert v-else type="info">Результаты анализа отсутствуют</v-alert>

    <v-dialog v-model="uploadDialog.visible" max-width="700px">
      <v-card>
        <v-card-title>Загрузка изображений</v-card-title>
        <v-card-text>
          <RawImageUploadForm ref="formRawImageUploadRef" v-model="uploadDialog.entries"
            :deviceId="session.device?.id" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="uploadDialog.visible = false">Отмена</v-btn>
          <v-btn color="primary" @click="submitImageUpload">Загрузить</v-btn>
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

    <v-dialog v-model="confirmDeleteManyDialog.visible" max-width="400px">
      <v-card>
        <v-card-title class="text-h6">Удаление всех изображений</v-card-title>
        <v-card-text>Вы уверены, что хотите удалить все изображения?</v-card-text>
        <v-card-actions class="justify-end">
          <v-btn text @click="confirmDeleteManyDialog.visible = false">Отмена</v-btn>
          <v-btn color="red" @click="deleteManyImage">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </template>
</template>

<script setup>
import { onMounted, ref, computed } from "vue";
import { format } from "date-fns";
import ru from "date-fns/locale/ru";

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
const session = ref(null);

import { useRawImageStore } from "@/stores/rawImage";
const rawImageStore = useRawImageStore();

const breadcrumbs = computed(() => [
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

// --- ЗАГРУЗКА ИСХОДНЫХ ИЗОБРАЖЕНИЙ ---

// Объект модального окна
const uploadDialog = ref({
  visible: false,
  entries: [],
});

// Открытие модального окна
const openUploadDialog = () => {
  uploadDialog.value = {
    visible: true,
    entries: [],
  };
};

// Загрузка исходных изображений
const formRawImageUploadRef = ref();

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
    const patientId = route.params.patient_id || "";
    session.value = await sessionStore.loadSessionDetailed(patientId, route.params.id);

    showSuccess("Изображения успешно загружены");
    uploadDialog.value.visible = false;
  }
};

// --- УДАЛЕНИЕ ИСХОДНЫХ ИЗОБРАЖЕНИЙ ---

// Объект модального окна
const confirmDeleteDialog = ref({
  visible: false,
  image: null,
});

// Открытие модальног окна
const openDeleteDialog = (image) => {
  confirmDeleteDialog.value = {
    visible: true,
    image,
  };
};

// Удаление изображения
const deleteImage = async () => {
  if (!confirmDeleteDialog.value.image) return;

  await rawImageStore.deleteRawImage(confirmDeleteDialog.value.image.id);

  confirmDeleteDialog.value.visible = false;
  confirmDeleteDialog.value.image = null;

  const patientId = route.params.patient_id || "";
  session.value = await sessionStore.loadSessionDetailed(patientId, route.params.id);

  showSuccess("Изображение удалено");
};

// --- УДАЛЕНИЕ ВСЕХ ИСХОДНЫХ ИЗОБРАЖЕНИЙ ---

// Объект модального окна
const confirmDeleteManyDialog = ref({
  visible: false,
  images: [],
});

// Открытие модальног окна
const openDeleteManyDialog = () => {
  confirmDeleteManyDialog.value = {
    visible: true,
    images: session.value.raw_images.map(i => i.id),
  };
};

// Удаление изображений
const deleteManyImage = async () => {
  if (!confirmDeleteManyDialog.value.images.length) return;

  const result = await rawImageStore.deleteManyRawImage({ ids: [...confirmDeleteManyDialog.value.images] });
  if (!result) return;

  confirmDeleteManyDialog.value.visible = false;
  confirmDeleteManyDialog.value.image = null;

  const patientId = route.params.patient_id || "";
  session.value = await sessionStore.loadSessionDetailed(patientId, route.params.id);

  showSuccess("Изображение удалено");
};

</script>