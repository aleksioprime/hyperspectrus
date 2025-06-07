<template>
  <h1>Конфигурации устройств</h1>

  <v-container fluid>
    <v-row>
      <!-- Левая часть: устройства и спектры -->
      <v-col cols="12" md="4" class="pa-0">
        <!-- Список устройств -->
        <v-card class="mb-4">
          <v-card-title>Устройства</v-card-title>
          <v-list>
            <v-list-item v-for="device in devices" :key="device.id" :active="selectedDevice?.id === device.id"
              @click="selectDevice(device)" clickable>
              <v-list-item-title>{{ device.name }}</v-list-item-title>
              <v-list-item-subtitle v-if="device.description">{{ device.description
                }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>

        <!-- Список спектров выбранного устройства -->
        <v-card v-if="selectedDevice">
          <v-card-title>Спектры устройства</v-card-title>
          <v-list>
            <v-list-item v-for="spectrum in spectra" :key="spectrum.id" @click="toggleSpectrum(spectrum)"
              :active="selectedSpectraIds.includes(spectrum.id)" clickable>
              <v-list-item-title>{{ spectrum.name }}</v-list-item-title>
              <v-list-item-subtitle>{{ spectrum.range }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- Правая часть: матрица перекрытий -->
      <v-col cols="12" md="8" class="pa-0">
        <v-card>
          <v-card-title>Матрица перекрытий</v-card-title>
          <v-table>
            <thead>
              <tr>
                <th>Спектр</th>
                <th v-for="chromophore in chromophores" :key="chromophore.id">
                  {{ chromophore.name }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="spectrum in selectedSpectra" :key="spectrum.id">
                <td>{{ spectrum.name }}</td>
                <td v-for="chromophore in chromophores" :key="chromophore.id"
                  :style="getCellStyle(spectrum, chromophore)">
                  {{ getOverlapValue(spectrum, chromophore) }}
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>

</template>

<script setup>
import { ref, computed, onMounted } from "vue";

// Тут предполагается, что есть patientStore, deviceStore и т.д.
import { useDeviceStore } from "@/stores/device";
import { useSpectrumStore } from "@/stores/spectrum";
import { useChromophoreStore } from "@/stores/chromophore";
import { useOverlapMatrixStore } from "@/stores/overlapMatrix"; // Например, матрица перекрытий

const deviceStore = useDeviceStore();
const spectrumStore = useSpectrumStore();
const chromophoreStore = useChromophoreStore();
const overlapMatrixStore = useOverlapMatrixStore();

const devices = ref([]);
const spectra = ref([]);
const chromophores = ref([]);
const overlapMatrix = ref({}); // { [spectrumId]: { [chromophoreId]: value } }

const selectedDevice = ref(null);
const selectedSpectraIds = ref([]);

const selectedSpectra = computed(() =>
  spectra.value.filter((s) => selectedSpectraIds.value.includes(s.id))
);

const selectDevice = async (device) => {
  selectedDevice.value = device;
  // Загрузить спектры для устройства
  spectra.value = await spectrumStore.loadSpectra({ device_id: device.id });
  selectedSpectraIds.value = [];
};

const toggleSpectrum = (spectrum) => {
  const i = selectedSpectraIds.value.indexOf(spectrum.id);
  if (i === -1) selectedSpectraIds.value.push(spectrum.id);
  else selectedSpectraIds.value.splice(i, 1);
};

const getOverlapValue = (spectrum, chromophore) => {
  return (
    overlapMatrix.value?.[spectrum.id]?.[chromophore.id] ?? "-"
  );
};

const getCellStyle = (spectrum, chromophore) => {
  // Например, визуализация по интенсивности
  const val = getOverlapValue(spectrum, chromophore);
  if (typeof val === "number") {
    // Чем выше значение, тем насыщеннее фон
    const intensity = Math.min(1, val / 100); // scale по своему
    return { background: `rgba(33,150,243,${intensity * 0.3})` };
  }
  return {};
};

onMounted(async () => {
  devices.value = await deviceStore.loadDevices();
  chromophores.value = await chromophoreStore.loadChromophores();
  overlapMatrix.value = await overlapMatrixStore.loadMatrix();
});

</script>