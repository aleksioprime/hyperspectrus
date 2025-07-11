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
      <v-col cols="12" sm="4">
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
      <v-col cols="12" sm="8">
        <div class="d-flex align-center">
          <div><strong>Заметки:</strong></div>
          <v-btn icon size="small" variant="text" color="primary" class="ms-2" @click="startEditNotes"
            title="Редактировать">
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
        </div>
        <div>
          <template v-if="!editingNotes">
            <span style="white-space: pre-line;">{{ session.notes || '—' }}</span>
          </template>
          <template v-else>
            <v-textarea v-model="editedNotes" auto-grow rows="2" hide-details class="my-2"
              @keydown.esc.stop="cancelEditNotes"></v-textarea>
            <div class="d-flex gap-2">
              <v-btn color="primary" size="small" @click="saveNotes" :loading="savingNotes">Сохранить</v-btn>
              <v-btn color="secondary" size="small" class="ms-2" @click="cancelEditNotes"
                :disabled="savingNotes">Отмена</v-btn>
            </div>
          </template>
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
        <!-- Сетка изображений -->
        <div class="d-flex flex-wrap gap-4">
          <div v-for="img in session.raw_images" :key="img.id"
            style="width: 150px; position: relative; text-align: center;" class="pa-1">
            <div style="position: relative;">
              <!-- Изображение с фиксированным размером -->
              <v-img :src="img.file_path" width="150" height="150" cover class="rounded img-thumb"
                @click="openImageDialog(img.file_path)">
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
                style="top: 4px; right: 4px; z-index: 2;" :disabled="!!session.processing_task_id">
                <v-icon size="18">mdi-delete</v-icon>
              </v-btn>
            </div>
            <!-- Подпись под изображением -->
            <div class="mt-1" style="font-size: 14px; color: #888;">
              {{ img.spectrum?.wavelength ? img.spectrum.wavelength + ' нм' : '—' }}
            </div>
          </div>
        </div>
        <!-- Кнопки управления -->
        <div>
          <div v-if="session.raw_images.length" class="d-flex align-center">
            <v-btn color="warning" @click="openDeleteManyDialog" :disabled="!!session.processing_task_id">
              <v-icon start>mdi-delete</v-icon>
              Удалить
            </v-btn>
            <v-btn color="primary" :loading="processing" @click="confirmStartProcessingDialog = true" class="ms-2"
              v-if="session && session.raw_images.length" :disabled="!!session.processing_task_id">
              <v-icon start>mdi-cogs</v-icon>
              Запустить обработку
            </v-btn>
          </div>
          <v-btn v-else color="secondary" @click="openUploadDialog">
            <v-icon start>mdi-upload</v-icon>
            Загрузить
          </v-btn>
        </div>
      </v-col>

      <!-- Блок обработанных изображений -->
      <v-col cols="12" md="6">
        <strong>Восстановленные изображения:</strong>
        <!-- Анимация ожидания обработки -->
        <div v-if="['PENDING', 'STARTED'].includes(session.processing_status)" class="d-flex align-center my-2">
          <v-progress-circular indeterminate color="primary" size="24" class="me-2" />
          <span class="text-grey">Изображения формируются...</span>
        </div>
        <!-- Нет изображений  -->
        <div v-else-if="!session.reconstructed_images?.length">
          <v-chip color="grey" size="small" class="my-2">нет данных</v-chip>
        </div>
        <!-- Сетка изображений -->
        <div v-else class="d-flex flex-wrap gap-4">
          <div v-for="img in session.reconstructed_images" :key="img.id"
            style="width: 150px; position: relative; text-align: center;" class="pa-1">
            <div style="position: relative;">
              <!-- Изображение с фиксированным размером -->
              <v-img :src="img.file_path" width="150" height="150" cover class="rounded img-thumb"
                @click="openImageDialog(img.file_path)">
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
              <!-- <v-btn icon color="red" size="small" @click="openDeleteDialog(img)" class="position-absolute"
                style="top: 4px; right: 4px; z-index: 2;">
                <v-icon size="18">mdi-delete</v-icon>
              </v-btn> -->
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

    <!-- Анимация, если задача в процессе -->
    <div v-if="['PENDING', 'STARTED'].includes(session.processing_status)">
      <div class="my-2 d-flex align-center">
        <v-progress-circular indeterminate color="primary" size="24" class="me-2" />
        <span class="text-grey">
          {{
            session.processing_status === 'RETRY'
              ? 'Повтор обработки...'
              : 'Анализируется...'
          }}
        </span>
      </div>
    </div>

    <!-- Ошибка -->
    <v-alert v-else-if="session.processing_status === 'FAILURE'" type="error" class="my-2" icon="mdi-alert"
      border="start">
      Обработка завершилась с ошибкой.
      <template v-if="processStatus?.error">
        <div class="text-error mt-1">Ошибка: {{ processStatus.error }}</div>
      </template>
    </v-alert>

    <!-- Успешный результат -->
    <div v-else-if="session.processing_status === 'SUCCESS' && session.result">
      <v-row>
        <v-col cols="12" sm="4">
          <div v-if="session?.result?.contour_path">
            <v-img :src="session.result.contour_path" width="300" height="300" cover class="rounded my-2 img-thumb"
              @click="openImageDialog(session.result.contour_path)">
              <template #placeholder>
                <v-skeleton-loader type="image" />
              </template>
              <template #error>
                <div class="d-flex align-center justify-center" style="height: 300px; background-color: #f5f5f5;">
                  <v-icon color="grey" size="48">mdi-image-off</v-icon>
                </div>
              </template>
            </v-img>
          </div>
          <div v-else>
            <v-chip color="grey" size="small" class="my-2">нет изображения</v-chip>
          </div>
        </v-col>
        <v-col cols="12" sm="8">
          <div class="my-2">
            <strong>Коэффициент S:</strong> {{ session.result.s_coefficient }}
          </div>
          <div class="my-2">
            <strong>THb (поражение):</strong> {{ session.result.mean_lesion_thb }}
          </div>
          <div class="my-2">
            <strong>THb (кожа):</strong> {{ session.result.mean_skin_thb }}
          </div>
        </v-col>
      </v-row>
    </div>

    <!-- Нет результата, но задача завершена -->
    <v-alert v-else-if="session.processing_status === 'SUCCESS'" type="info" class="my-2">
      Обработка завершена, но результат отсутствует.
    </v-alert>

    <!-- Нет задачи вообще -->
    <v-alert v-else type="info" class="my-2">
      Результаты анализа отсутствуют
    </v-alert>

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

    <v-dialog v-model="confirmStartProcessingDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h6">Подтверждение запуска</v-card-title>
        <v-card-text>
          Вы уверены, что хотите запустить обработку данных?
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn text @click="confirmStartProcessingDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="processing" @click="handleStartProcessing">Запустить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogImage.visible" max-width="800px" persistent>
      <v-card class="pa-2" style="background: rgba(0,0,0,0.95);">
        <v-img :src="dialogImage.src" max-width="100%" max-height="80vh" cover @click="closeImageDialog" />
        <v-card-actions>
          <v-spacer />
          <v-btn color="white" variant="text" @click="closeImageDialog">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </template>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from "vue";
import { format } from "date-fns";
import ru from "date-fns/locale/ru";

import logger from '@/common/helpers/logger';

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

const formatDateTime = (dateStr) => {
  return format(new Date(dateStr), "d MMMM yyyy HH:mm", { locale: ru });
};

// --- РЕДАКТИРОВАНИЕ ЗАМЕТОК ---

const editingNotes = ref(false);
const editedNotes = ref("");
const savingNotes = ref(false);

function startEditNotes() {
  editingNotes.value = true;
  editedNotes.value = session.value?.notes || "";
}

function cancelEditNotes() {
  editingNotes.value = false;
  editedNotes.value = session.value?.notes || "";
}

async function saveNotes() {
  if (!session.value) return;
  savingNotes.value = true;
  await sessionStore.updateSession(session.value.patient?.id, session.value.id, {
    notes: editedNotes.value,
  });
  session.value.notes = editedNotes.value;
  editingNotes.value = false;
  savingNotes.value = false;
}

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
  const valid = await formRawImageUploadRef.value?.submit();
  if (!valid) return;

  const formData = new FormData();

  formData.append("session_id", session.value?.id);

  uploadDialog.value.entries.forEach((entry) => {
    formData.append("spectrum_ids", entry.spectrum_id);
    formData.append("files", entry.file);
  });

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

  startStatusPolling();
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

  startStatusPolling();
};

// --- ЗАПУСК И ПРОВЕРКА ЗАДАЧИ ---

const confirmStartProcessingDialog = ref(false);

const handleStartProcessing = async () => {
  confirmStartProcessingDialog.value = false;
  await startProcessing();
};

const processing = ref(false);      // Состояние кнопки и процесса
const processStatus = ref(null);    // Текущий статус задачи
let statusInterval = null;          // Таймер для пулинга

// Запуск задачи обработки
const startProcessing = async () => {
  if (!session.value) return;
  processing.value = true;

  processStatus.value = null;

  const result = await sessionStore.processSession(
    session.value.patient?.id,
    session.value.id
  );

  if (!result) {
    snackbar.text = "Ошибка запуска обработки";
    snackbar.show = true;
  }

  if (result.task_id) {
    await reloadSession();
    startStatusPolling();
  }

  processing.value = false;

};

// Функция обновления данных сеанса
const reloadSession = async () => {
  const patientId = route.params.patient_id || "";
  session.value = await sessionStore.loadSessionDetailed(patientId, route.params.id);
};

// Пулинг статуса задачи обработки
const checkProcessingStatus = async () => {
  if (!["PENDING", "STARTED"].includes(session.value?.processing_status)) return;

  processStatus.value = await sessionStore.processSessionStatus(
    session.value.patient?.id,
    session.value.id
  );

  logger.info("Процесс обработки запустился: ", processStatus.value)

  if (
    !processStatus.value ||
    processStatus.value?.celery_status === "SUCCESS" ||
    processStatus.value?.celery_status === "FAILURE" ||
    processStatus.value?.status === "NO_TASK"
  ) {
    stopStatusPolling();
    await reloadSession();
  }
};

// Запуск и остановка интервала проверки статуса
const startStatusPolling = () => {
  stopStatusPolling();
  statusInterval = setInterval(checkProcessingStatus, 2500);
};
const stopStatusPolling = () => {
  if (statusInterval) clearInterval(statusInterval);
  statusInterval = null;
};

// Слежение за появлением ID задачи в сессии для старта пуллинга
watch(
  () => session.value?.processing_status,
  (newVal) => {
    if (["PENDING", "STARTED"].includes(newVal)) startStatusPolling();
    else stopStatusPolling();
  }
);


// --- ПРОСМОТР ИЗОБРАЖЕНИЙ ---

const dialogImage = ref({ visible: false, src: null });

function openImageDialog(src) {
  dialogImage.value = {
    visible: true,
    src,
  };
}

function closeImageDialog() {
  dialogImage.value.visible = false;
  dialogImage.value.src = null;
}

onMounted(async () => {
  const patientId = route.params.patient_id || "";
  session.value = await sessionStore.loadSessionDetailed(patientId, route.params.id);

  if (["PENDING", "STARTED"].includes(session.value?.processing_status)) {
    startStatusPolling();
  }
});

onUnmounted(() => {
  stopStatusPolling();
});

</script>

<style scoped>
.img-thumb {
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 0 0px rgba(0, 0, 0, 0);
  /* no shadow by default */
}

.img-thumb:hover {
  transform: scale(1.07);
  box-shadow: 0 4px 24px 0 rgba(50, 120, 200, 0.15);
  z-index: 2;
  cursor: pointer;
}
</style>