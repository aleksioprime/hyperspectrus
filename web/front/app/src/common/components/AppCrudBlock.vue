<template>
  <!-- Блок существующих объектов -->
  <template v-if="objects.length">
    <div v-for="obj in objects" :key="obj.id" class="mb-2">
      <div :class="{ 'border-danger': obj.id === deletingObjectId }" class="border rounded p-2">
        <slot name="data" :obj="obj" :handleUpdate="handleUpdate" :locked="editingLocked"></slot>
      </div>
      <div class="d-flex justify-content-end">
        <app-toast :show="deletingObjectId === obj.id" @confirm="deleteObjectConfirm" @cancel="deleteObjectCancel"
          :isLoading="isProcessDeleting">
          Удалить эту запись?
        </app-toast>
        <app-button class="btn btn-sm btn-link p-0" @click="deleteObject(obj.id)" :disabled="newObject || locked">
          Удалить
        </app-button>
      </div>
    </div>
  </template>
  <template v-else>
    <div v-if="!newObject" class="d-flex align-items-center justify-content-center border rounded p-3 mb-2">
      <slot name="no-data">Нет данных</slot>
    </div>
  </template>

  <!-- Блок добавления нового объекта -->
  <div id="newObject">
    <slot name="new" :newObject="newObject"></slot>
  </div>

  <!-- Блок кнопок -->
  <div class="d-flex align-items-center">
    <div v-if="newObject">
      <div v-if="hasCreateErrors" class="mb-2 text-danger">Неверные данные!</div>
      <div class="d-flex align-items-center py-3">
        <div class="me-2">Сохранить?</div>
        <app-button class="btn btn-sm btn-success me-2" @click="saveNewObject"
          :isLoading="isProcessCreating">Сохранить</app-button>
        <app-button class="btn btn-sm btn-secondary" @click="cancelNewObject">Отмена</app-button>
      </div>
    </div>
    <app-button v-else class="btn btn-sm btn-primary ms-auto" @click="addNewObject"
      :disabled="editingLocked && !newObject">
      <span>Добавить</span>
    </app-button>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import logger from '@/common/helpers/logger';

const props = defineProps({
  objects: Array,
  fetchCreate: Function,
  fetchUpdate: Function,
  fetchDelete: Function,
  defaultFields: Object,
  requiredFields: Array,
  locked: Boolean,
});

const emit = defineEmits(["update", "update:locked"]);

const editingLocked = ref(props.locked);
watch(() => props.locked, (newValue) => editingLocked.value = newValue);
watch(() => editingLocked.value, (newValue) => emit("update:locked", newValue));

const newObject = ref(null);
const hasCreateErrors = ref(false);
const isProcessCreating = ref(false);
const deletingObjectId = ref(null);
const isProcessDeleting = ref(false);

const addNewObject = () => {
  newObject.value = { ...props.defaultFields };
  emit('update:locked', true);

  // Ждём обновления DOM и выполняем скролл
  nextTick(() => {
    const newObjectElement = document.getElementById("newObject");
    if (newObjectElement) {
      newObjectElement.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
};

const saveNewObject = async () => {
  if (isProcessCreating.value) return;
  hasCreateErrors.value = false;

  if (props.requiredFields.some(field => !newObject.value?.[field])) {
    hasCreateErrors.value = true;
    return;
  }

  isProcessCreating.value = true;
  const result = await props.fetchCreate(newObject.value);
  isProcessCreating.value = false;

  if (!result) {
    logger.error("Ошибка добавления данных");
    return;
  }

  logger.info("Данные успешно добавлены");
  emit("update");
  cancelNewObject();
};

const cancelNewObject = () => {
  newObject.value = null;
  hasCreateErrors.value = false;
  emit("update:locked", false);
};

const handleUpdate = async (editData, id) => {
  const result = await props.fetchUpdate(id, editData);
  if (!result) {
    logger.error("Ошибка редактирования данных");
    return;
  }
  emit("update");
};

const deleteObject = (id) => {
  deletingObjectId.value = id;
  editingLocked.value = true;
};

const deleteObjectConfirm = async () => {
  if (isProcessDeleting.value) return;

  isProcessDeleting.value = true;
  const result = await props.fetchDelete(deletingObjectId.value);
  isProcessDeleting.value = false;

  if (!result) {
    logger.error("Ошибка удаления данных");
    return;
  }

  logger.info("Данные успешно удалены");
  emit("update");
  deleteObjectCancel();
};

const deleteObjectCancel = () => {
  deletingObjectId.value = null;
  editingLocked.value = false;
};
</script>