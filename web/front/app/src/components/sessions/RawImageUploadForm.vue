<template>
  <div>
    <v-btn color="primary" @click="addEntry">
      <v-icon start>mdi-plus</v-icon>
      Добавить изображение
    </v-btn>

    <v-divider class="my-4" />
    <v-form @submit.prevent="submit" ref="formRef">
      <div v-for="(entry, index) in formEntries" :key="index" class="mb-4">
        <v-row dense>
          <v-col cols="12" sm="5">
            <v-select v-model="entry.spectrum_id" :items="spectrumOptions" item-title="wavelength" item-value="id"
              label="Спектр" :rules="[v => !!v || 'Обязательное поле']" required />
          </v-col>
          <v-col cols="12" sm="5">
            <v-file-input v-model="entry.file" label="Файл изображения" accept="image/*"
              :rules="[v => !!v || 'Выберите файл']" required />
          </v-col>
          <v-col cols="12" sm="2">
            <v-btn icon color="red" @click="removeEntry(index)" v-if="formEntries.length > 1">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </div>
    </v-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from "vue";
import { useSpectrumStore } from "@/stores/spectrum";

const props = defineProps({
  modelValue: Array,
  deviceId: String
});

const emit = defineEmits(["submit", "update:modelValue"]);

const spectrumStore = useSpectrumStore();
const spectrumOptions = ref([]);

const formEntries = ref([
  { spectrum_id: null, file: null },
]);

const formRef = ref();

const submit = async () => {
  const { valid } = await formRef.value.validate();

  console.log("Валидация: ", valid)

  if (!valid) {
    console.warn("Форма не прошла валидацию");
    return; // <<< не отправляем, если есть ошибки
  }

  emit("submit");
};

const addEntry = () => {
  formEntries.value.push({ spectrum_id: null, file: null });
};

const removeEntry = (index) => {
  formEntries.value.splice(index, 1);
};

watch(formEntries, (newVal) => {
  emit("update:modelValue", newVal);
}, { deep: true });

onMounted(async () => {
  spectrumOptions.value = await spectrumStore.loadSpectra(props.deviceId);
});

defineExpose({
  submit,
});
</script>