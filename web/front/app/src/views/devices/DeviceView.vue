<template>
  <h1 class="text-h5 mb-4">Конфигурации устройств</h1>

  <v-container fluid>
    <v-row>
      <v-col cols="12" md="4">
        <!-- Список устройств -->
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center justify-between">
            <div>Устройства</div>
            <v-btn icon size="small" color="primary" class="ma-1 ms-auto" @click="openEditDeviceDialog()">
              <v-icon>mdi-plus</v-icon>
            </v-btn>
          </v-card-title>
          <v-list>
            <v-list-item v-for="device in devices" :key="device.id" :active="selectedDevice?.id === device.id"
              @click="selectDevice(device)" clickable>
              <v-list-item-title>{{ device.name }}</v-list-item-title>
              <v-list-item-subtitle v-if="device.description">
                {{ device.description }}
              </v-list-item-subtitle>
              <template #append>
                <v-btn icon size="small" class="ma-1" @click.stop="openEditDeviceDialog(device)">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-menu v-model="deleteMenu[device.id]" :close-on-content-click="false" location="bottom" offset="8">
                  <template #activator="{ props }">
                    <v-btn icon size="small" class="ma-1" color="red" v-bind="props" @click.stop>
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </template>
                  <v-card>
                    <v-card-text class="text-center pb-1">
                      Удалить <b>{{ device.name }}</b>?
                    </v-card-text>
                    <v-card-actions class="justify-end pt-0">
                      <v-btn size="small" @click="deleteMenu[device.id] = false">Отмена</v-btn>
                      <v-btn size="small" color="red" @click="confirmDeleteDevice(device)">Удалить</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-menu>
              </template>
            </v-list-item>
          </v-list>
        </v-card>

        <!-- Список спектров выбранного устройства -->
        <v-card v-if="selectedDevice">
          <v-card-title class="d-flex align-center justify-between">
            <div>Спектры</div>
            <v-btn icon size="small" color="primary" class="ma-1 ms-auto" @click="openEditSpectrumDialog()">
              <v-icon>mdi-plus</v-icon>
            </v-btn>
          </v-card-title>
          <v-list>
            <v-list-item v-for="spectrum in spectra" :key="spectrum.id">
              <v-list-item-subtitle>
                {{ spectrum.wavelength }} <span v-if="!!spectrum.name">({{ spectrum.name }})</span>
              </v-list-item-subtitle>
              <template #append>
                <v-btn icon size="small" class="ma-1" @click.stop="openEditSpectrumDialog(spectrum)">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-menu v-model="deleteSpectrumMenu[spectrum.id]" :close-on-content-click="false" location="bottom"
                  offset="8">
                  <template #activator="{ props }">
                    <v-btn icon size="small" class="ma-1" color="red" v-bind="props" @click.stop>
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </template>
                  <v-card>
                    <v-card-text class="text-center pb-1">
                      Удалить <b>{{ spectrum.wavelength }}</b>?
                    </v-card-text>
                    <v-card-actions class="justify-end pt-0">
                      <v-btn size="small" @click="deleteSpectrumMenu[spectrum.id] = false">Отмена</v-btn>
                      <v-btn size="small" color="red" @click="confirmDeleteSpectrum(spectrum)">Удалить</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-menu>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <!-- Матрица коэффициентов -->
          <v-card-title>Матрица перекрытий</v-card-title>
          <v-table>
            <thead>
              <tr>
                <th>Спектр</th>
                <th v-for="chromophore in chromophores" :key="chromophore.id" class="text-center">
                  <v-tooltip location="top" open-delay="300">
                    <template #activator="{ props }">
                      <span v-bind="props" style="cursor: help;">
                        {{ chromophore.symbol }}
                      </span>
                    </template>
                    <span>{{ chromophore.name }}</span>
                  </v-tooltip>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="spectrum in spectra" :key="spectrum.id">
                <td>
                  <v-tooltip location="top" open-delay="300">
                    <template #activator="{ props }">
                      <span v-bind="props" style="cursor: help;">
                        {{ spectrum.wavelength }}
                      </span>
                    </template>
                    <span>{{ spectrum.name }}</span>
                  </v-tooltip>
                </td>
                <td v-for="chromophore in chromophores" :key="chromophore.id" :class="[
                  'overlap-cell',
                  isEditingCell(spectrum, chromophore) && 'overlap-cell--editing'
                ]" @click="startEditCell(spectrum, chromophore, $event)">
                  <template v-if="isEditingCell(spectrum, chromophore)">
                    <input :ref="el => setEditInputRef(el, spectrum, chromophore)" v-model.number="editingValue"
                      class="no-border-input" type="number" min="0" step="any" @blur="saveCell(spectrum, chromophore)"
                      @keyup.enter="blurEditInput" @keyup.esc="cancelEditCell" />
                  </template>
                  <template v-else>
                    {{ getOverlapValue(spectrum, chromophore) }}
                  </template>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
        <v-btn v-if="authStore.isSuperuser" color="secondary" variant="outlined" size="small" class="my-3" @click="fillMatrixRandomly"
          :loading="randomFillLoading">
          <v-icon start>mdi-dice-multiple</v-icon>
          Заполнить матрицу случайно
        </v-btn>
      </v-col>
    </v-row>
  </v-container>

  <!-- Модальное окно создания/редактирования устройства -->
  <v-dialog v-model="modalDeviceDialog.visible" max-width="400px">
    <v-card>
      <v-card-title>
        {{ modalDeviceDialog.editing ? 'Редактировать устройство' : 'Новое устройство' }}
      </v-card-title>
      <v-card-text>
        <v-form ref="deviceFormRef" v-model="deviceFormValid">
          <v-text-field v-model="modalDeviceDialog.form.name" :rules="[v => !!v || 'Укажите название']"
            label="Название устройства" required dense />
        </v-form>
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn size="small" @click="modalDeviceDialog.visible = false">Отмена</v-btn>
        <v-btn size="small" color="primary" @click="submitDeviceDialog">
          {{ modalDeviceDialog.editing ? 'Сохранить' : 'Создать' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Модальное окно создания/редактирования спектра -->
  <v-dialog v-model="modalSpectrumDialog.visible" max-width="400px">
    <v-card>
      <v-card-title>
        {{ modalSpectrumDialog.editing ? "Редактировать спектр" : "Новый спектр" }}
      </v-card-title>
      <v-card-text>
        <v-form ref="spectrumFormRef" v-model="spectrumFormValid">
          <v-text-field v-model="modalSpectrumDialog.form.name" :rules="[v => !!v || 'Укажите название']"
            label="Название спектра" required dense />
          <v-text-field v-model.number="modalSpectrumDialog.form.wavelength" :rules="[
            v => !!v || 'Укажите длину волны',
            v => v > 0 || 'Длина волны должна быть положительной',
          ]" label="Длина волны (нм)" type="number" required dense />
        </v-form>
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn size="small" @click="modalSpectrumDialog.visible = false">Отмена</v-btn>
        <v-btn size="small" color="primary" @click="submitSpectrumDialog">
          {{ modalSpectrumDialog.editing ? "Сохранить" : "Создать" }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";

import logger from '@/common/helpers/logger';

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();

import { useDeviceStore } from "@/stores/device";
const deviceStore = useDeviceStore();
const devices = ref([]);

import { useSpectrumStore } from "@/stores/spectrum";
const spectrumStore = useSpectrumStore();

import { useChromophoreStore } from "@/stores/chromophore";
const chromophoreStore = useChromophoreStore();
const chromophores = ref([]);

import { useOverlapMatrixStore } from "@/stores/overlapMatrix";
const overlapMatrixStore = useOverlapMatrixStore();

const selectedDevice = ref(null);

// Список спектров выбранного устройства (берём из выбранного устройства)
const spectra = computed(() => selectedDevice.value?.spectra || []);

// При выборе устройства просто подставляем его spectra
const selectDevice = async (device) => {
  localStorage.setItem("selectedDeviceId", device.id);
  const detailed = await deviceStore.loadDeviceDetailed(device.id);
  selectedDevice.value = detailed;
};

// Собираем матрицу: { [spectrumId]: { [chromophoreId]: coefficient } }
const overlapMatrix = computed(() => {
  const matrix = {};
  for (const spectrum of spectra.value) {
    if (!matrix[spectrum.id]) matrix[spectrum.id] = {};
    // Исправление здесь:
    const overlaps = Array.isArray(spectrum.overlaps) ? spectrum.overlaps : [];
    for (const overlap of overlaps) {
      matrix[spectrum.id][overlap.chromophore_id] = overlap.coefficient;
    }
  }
  return matrix;
});

// Возвращаем значение для ячейки
const getOverlapValue = (spectrum, chromophore) => {
  return (
    overlapMatrix.value?.[spectrum.id]?.[chromophore.id] ?? "-"
  );
};

const getCellStyle = (spectrum, chromophore) => {
  const val = getOverlapValue(spectrum, chromophore);
  if (typeof val === "number") {
    const intensity = Math.min(1, val / 100);
    return { background: `rgba(33,150,243,${intensity * 0.3})` };
  }
  return {};
};

// При инициализации получаем устройства и хромофоры
onMounted(async () => {
  devices.value = await deviceStore.loadDevices();
  chromophores.value = await chromophoreStore.loadChromophores();
  // Восстанавливаем выбранное устройство по id из localStorage
  const savedDeviceId = localStorage.getItem("selectedDeviceId");
  if (savedDeviceId && devices.value.some(d => d.id === savedDeviceId)) {
    await selectDevice(devices.value.find(d => d.id === savedDeviceId));
  }
});

// --- СОЗДАНИЕ/РЕДАКТИРОВАНИЕ УСТРОЙСТВ ---

const deviceFormRef = ref();
const deviceFormValid = ref(true);

const modalDeviceDialog = ref({
  visible: false,
  editing: false,
  form: {
    id: null,
    name: ""
  }
});

// Вызов диалогового окна создания/редактирования устройства
const openEditDeviceDialog = (device = null) => {
  modalDeviceDialog.value = {
    visible: true,
    editing: !!device,
    form: device
      ? { id: device.id, name: device.name }
      : { id: null, name: "" }
  };
};

// Подтверждение создания/редактирование устройства
const submitDeviceDialog = async () => {
  const valid = await deviceFormRef.value?.validate();
  if (!valid) return;

  const { form, editing } = modalDeviceDialog.value;

  if (editing) {
    logger.info("Редактирование устройства: ", form.name)

    const result = await deviceStore.updateDevice(form.id, { name: form.name });

    if (!result) return;

    const index = devices.value.findIndex((d) => d.id === form.id);
    if (index !== -1) devices.value[index].name = form.name;

    if (selectedDevice.value?.id === form.id) selectedDevice.value.name = form.name;

  } else {
    logger.info("Создание устройства: ", form.name)

    const newDevice = await deviceStore.createDevice({ name: form.name });

    if (!newDevice) return;

    devices.value.unshift(newDevice);
  }

  modalDeviceDialog.value.visible = false;
};

// --- УДАЛЕНИЕ УСТРОЙСТВА ---
const deleteMenu = ref({});

// Подтверждение удаления утсройства
const confirmDeleteDevice = async (device) => {
  const success = await deviceStore.deleteDevice(device.id);
  if (success) {
    devices.value = devices.value.filter(d => d.id !== device.id);
    if (selectedDevice.value?.id === device.id) {
      selectedDevice.value = null;
      localStorage.removeItem("selectedDeviceId");
    }
  }
  deleteMenu.value[device.id] = false;
};


// ---- СОЗДАНИЕ/РЕДАКТИРОВАНИЕ СПЕКТРОВ ----

const spectrumFormRef = ref();
const spectrumFormValid = ref(true);

const modalSpectrumDialog = ref({
  visible: false,
  editing: false,
  form: {
    id: null,
    name: "",
    wavelength: ""
  }
});

// Для меню подтверждения удаления
const deleteSpectrumMenu = ref({});

const openEditSpectrumDialog = (spectrum = null) => {
  if (!selectedDevice.value) return; // Без устройства нельзя создавать спектр!
  modalSpectrumDialog.value = {
    visible: true,
    editing: !!spectrum,
    form: spectrum
      ? { id: spectrum.id, name: spectrum.name, wavelength: spectrum.wavelength }
      : { id: null, name: "", wavelength: "" }
  };
};

const submitSpectrumDialog = async () => {
  const valid = await spectrumFormRef.value?.validate();
  if (!valid) return;
  const { form, editing } = modalSpectrumDialog.value;

  if (!selectedDevice.value) return; // safety

  if (editing) {
    // updateSpectrum(device_id, spectrum_id, { ... })
    const result = await spectrumStore.updateSpectrum(
      selectedDevice.value.id,
      form.id,
      { name: form.name, wavelength: form.wavelength }
    );
    if (!result) return;
    const idx = spectra.value.findIndex((s) => s.id === form.id);
    if (idx !== -1) {
      spectra.value[idx].name = form.name;
      spectra.value[idx].wavelength = form.wavelength;
    }
  } else {
    const newSpectrum = await spectrumStore.createSpectrum(selectedDevice.value.id, {
      name: form.name,
      wavelength: form.wavelength,
    });
    if (newSpectrum) spectra.value.unshift(newSpectrum);
  }
  modalSpectrumDialog.value.visible = false;
};

const confirmDeleteSpectrum = async (spectrum) => {
  const success = await spectrumStore.deleteSpectrum(selectedDevice.value.id, spectrum.id);
  if (success) {
    if (selectedDevice.value?.spectra) {
      selectedDevice.value.spectra = selectedDevice.value.spectra.filter(
        (s) => s.id !== spectrum.id
      );
    }
  }
  deleteSpectrumMenu.value[spectrum.id] = false;
};

// --- РАБОТА С МАТРИЦЕЙ КОЭФФИЦИЕНТОВ ---

// Состояние редактируемой ячейки
const editingCell = ref({ spectrumId: null, chromophoreId: null });

// Значение ячейки
const editingValue = ref("");

// Ссылка на элемент ввода значения в ячейке { spectrumId:chromophoreId }
const editInputRefs = ref({});

// Функция для сохранения ссылки на элемент ввода для конкретной ячейки матрицы
function setEditInputRef(el, spectrum, chromophore) {
  // Только для той ячейки, которая сейчас редактируется
  if (isEditingCell(spectrum, chromophore)) {
    editInputRefs.value[`${spectrum.id}:${chromophore.id}`] = el;
  }
}

// Программно снять фокус с элемента ввода (например, при нажатии Enter)
// Находим нужный элемент по ключу текущей редактируемой ячейки и вызываем снятие фокуса
function blurEditInput() {
  nextTick(() => {
    const { spectrumId, chromophoreId } = editingCell.value;
    const key = `${spectrumId}:${chromophoreId}`;
    const input = editInputRefs.value[key];
    if (input && input.blur) input.blur();
  });
}

// Начать редактирование выбранной ячейки
function startEditCell(spectrum, chromophore, evt) {
  // Если ячейка уже редактируется — ничего не делать
  if (!isEditingCell(spectrum, chromophore)) {
    // Сохраняем координаты редактируемой ячейки
    editingCell.value = { spectrumId: spectrum.id, chromophoreId: chromophore.id };

    // Вставляем текущее значение в поле ввода (если ячейка была пуста — "")
    const val = getOverlapValue(spectrum, chromophore);
    editingValue.value = val === "-" ? "" : val;
    originalEditingValue = editingValue.value;

    // После обновления DOM сразу фокусируемся на элементе ввода этой ячейки
    nextTick(() => {
      const key = `${spectrum.id}:${chromophore.id}`;
      const input = editInputRefs.value[key];
      if (input && input.focus) {
        input.focus();
        input.select();
      }
    });

    // Останавливаем всплытие события, чтобы не было лишних обработчиков
    evt?.stopPropagation();
  }
}

// Проверка — совпадает ли данная ячейка с редактируемой
function isEditingCell(spectrum, chromophore) {
  return (
    editingCell.value.spectrumId === spectrum.id &&
    editingCell.value.chromophoreId === chromophore.id
  );
}

let isEditCancelled = false;
let originalEditingValue = null;

// Сброс состояния редактирования — выходим из режима редактирования
function cancelEditCell() {
  isEditCancelled = true;
  editingCell.value = { spectrumId: null, chromophoreId: null };
  editingValue.value = "";
}

// Флаг, чтобы не допустить несколько параллельных сохранений
let saving = false;

// Сохранить значение из инпута в матрицу коэффициентов
async function saveCell(spectrum, chromophore) {

  // Если был cancel (например, через Esc), не сохраняем и сбрасываем флаг
  if (isEditCancelled) {
    isEditCancelled = false;
    editingCell.value = { spectrumId: null, chromophoreId: null };
    editingValue.value = "";
    return;
  }

  // Если уже идёт сохранение — выходим
  if (saving) return;
  saving = true;

  // Получаем новое значение из инпута ("" превращаем в null)
  const newVal = editingValue.value === "" ? null : Number(editingValue.value);
  // Предыдущее значение в матрице
  const oldVal = getOverlapValue(spectrum, chromophore);

  // Массив перекрытий для данного спектра
  const overlaps = Array.isArray(spectrum.overlaps) ? spectrum.overlaps : [];
  // Ищем перекрытие по id хромофора
  const overlapObj = overlaps.find((o) => o.chromophore_id === chromophore.id);

  // 1. Если уже есть такой overlap и новое значение не равно старому — обновляем
  if (overlapObj && newVal !== null && newVal !== oldVal) {
    const updated = await overlapMatrixStore.updateOverlapCoefficient(overlapObj.id, {
      coefficient: newVal,
    });
    if (updated) overlapObj.coefficient = newVal;

    // 2. Если такого overlap не было, но появилось новое значение — создаём новую запись
  } else if (!overlapObj && newVal !== null) {
    const created = await overlapMatrixStore.createOverlapCoefficient({
      spectrum_id: spectrum.id,
      chromophore_id: chromophore.id,
      coefficient: newVal,
    });
    if (created) overlaps.push(created);

    // 3. Если overlap был, но значение стало пустым/null — удаляем запись
  } else if (overlapObj && (newVal === null || newVal === "")) {
    const success = await overlapMatrixStore.deleteOverlapCoefficient(overlapObj.id);
    if (success) {
      // Удаляем overlap из массива спектра
      spectrum.overlaps = overlaps.filter((o) => o.chromophore_id !== chromophore.id);
    }
  }

  saving = false;
  editingCell.value = { spectrumId: null, chromophoreId: null };
  editingValue.value = "";
}

// --- ЗАПОЛНЕНИЕ МАТРИЦЫ СЛУЧАЙНЫМИ ЧИСЛАМИ ---

const randomFillLoading = ref(false);

async function fillMatrixRandomly() {
  if (!selectedDevice.value) return;
  try {
    randomFillLoading.value = true;
    // Запускаем запрос через стор устройства
    await deviceStore.randomFillOverlapsDevice(selectedDevice.value.id);
    // После успешного заполнения — обновляем детальные данные устройства
    const updated = await deviceStore.loadDeviceDetailed(selectedDevice.value.id);
    selectedDevice.value = updated;
  } catch (err) {
    logger.error("Ошибка при заполнении матрицы случайно:", err);
    // Можно показать toast/уведомление
  } finally {
    randomFillLoading.value = false;
  }
}

</script>

<style scoped>
.overlap-cell {
  cursor: pointer;
  transition: background 0.15s;
}

.overlap-cell:hover {
  background: #e3f2fd;
}

.overlap-cell--editing {
  background: #fff3cd !important;
  /* Например, светло-жёлтый (можно любой) */
  /* Можно добавить границу, если хочешь: */
  /* border: 2px solid #ffc107; */
  /* transition: background 0.2s; */
}

/* Фиксируем ширину столбцов таблицы */
th,
td.overlap-cell {
  min-width: 70px;
  max-width: 70px;
  width: 70px;
  text-align: center;
  box-sizing: border-box;
  /* Можно убрать или уменьшить паддинги */
  padding: 0;
}

/* Убираем лишние стили у input */
.no-border-input {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  border: none;
  outline: none;
  background: transparent;
  box-sizing: border-box;
  padding: 0;
  text-align: center;
  font: inherit;
  /* убираем стрелки у числового инпута */
  appearance: textfield;
}

.no-border-input::-webkit-outer-spin-button,
.no-border-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.no-border-input[type="number"] {
  -moz-appearance: textfield;
}
</style>