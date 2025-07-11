<template>
  <v-form ref="formRef" @submit.prevent="onSubmit">
    <v-text-field v-model="form.date" label="Дата и время сеанса" type="datetime-local" :rules="[rules.required]"
      required />
    <div v-if="isCreate">
      <v-select v-model="form.device_id" :items="devices" item-title="name" item-value="id" label="Устройство"
        :rules="[rules.required]" required />
    </div>
    <v-textarea v-model="form.notes" label="Заметки" rows="2" auto-grow/>
  </v-form>
</template>

<script setup>
import { ref, watch, reactive, onMounted } from "vue";
import rules from "@/common/helpers/rules";

import { useDeviceStore } from "@/stores/device";
const deviceStore = useDeviceStore();
const devices = ref([])

const props = defineProps({
  modelValue: Object,
  isCreate: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const form = reactive({
  date: "",
  device_id: "",
  operator_id: "",
  notes: "",
});

// Синхронизация изменения внешнего modelValue с внутренним
watch(
  () => props.modelValue?.id,
  (newId, oldId) => {
    if (newId !== oldId) {
      Object.assign(form, { ...props.modelValue });
    }
  },
  { immediate: true }
);

// Синхронизация изменения внутренего modelValue с внешним
watch(
  () => ({ ...form }),
  val => emit("update:modelValue", val)
);

// Валидация формы
const formRef = ref();

const onSubmit = async () => {
  const { valid } = await formRef.value?.validate();
  return valid
};

onMounted(async () => {
  devices.value = await deviceStore.loadDevices();
});

defineExpose({ submit: onSubmit });
</script>