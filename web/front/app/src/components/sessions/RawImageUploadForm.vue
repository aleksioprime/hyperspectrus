<template>
  <v-form @submit.prevent="onSubmit" ref="formRef">
    <div v-for="(entry, index) in formEntries" :key="entry.spectrum_id">
      <v-row dense>
        <v-col cols="12" sm="5">
          <v-text-field :model-value="`${entry.wavelength} нм`" label="Спектр" readonly />
        </v-col>
        <v-col cols="12" sm="7">
          <v-file-input v-model="entry.file" label="Файл изображения" accept="image/*" :rules="[rules.required]"
            required />
        </v-col>
      </v-row>
    </div>
  </v-form>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import rules from "@/common/helpers/rules";

import { useSpectrumStore } from "@/stores/spectrum";
const spectrumStore = useSpectrumStore();

const props = defineProps({
  modelValue: Array,
  deviceId: String
});

const emit = defineEmits(["update:modelValue"]);

const formEntries = ref([]);

// Синхронизация изменения внутренего modelValue с внешним
watch(formEntries, (newVal) => {
  emit("update:modelValue", newVal);
}, { deep: true });

// Валидация формы
const formRef = ref();

const onSubmit = async () => {
  const { valid } = await formRef.value.validate();
  return valid
};

onMounted(async () => {
  const spectra = await spectrumStore.loadSpectra(props.deviceId);

  formEntries.value = spectra.map(spectrum => ({
    spectrum_id: spectrum.id,
    wavelength: spectrum.wavelength,
    file: null
  }));

  emit("update:modelValue", formEntries.value);
});

defineExpose({ submit: onSubmit });
</script>