<template>
  <v-form @submit.prevent="submit" ref="formRef">
    <v-select v-model="form.device_id" :items="deviceOptions" item-title="name" item-value="id" label="Устройство"
      :rules="[v => !!v || 'Обязательное поле']" required />
    <v-text-field v-model="form.date" label="Дата и время сеанса" type="datetime-local"
      :rules="[v => !!v || 'Обязательное поле']" required />
    <v-textarea v-model="form.notes" label="Заметки" rows="2" />
  </v-form>
</template>

<script setup>
import { ref, watch, reactive, onMounted, computed } from "vue";

import { useDeviceStore } from "@/stores/device";
const deviceStore = useDeviceStore();

const props = defineProps({ modelValue: Object });
const emit = defineEmits(["submit", "update:modelValue"]);

const form = reactive({
  date: "",
  device_id: "",
  operator_id: "",
  notes: "",
});

const formRef = ref();

watch(() => props.modelValue, (val) => {
  if (val) Object.assign(form, val);
}, { immediate: true });

watch(form, () => {
  emit("update:modelValue", { ...form });
}, { deep: true });

const submit = async () => {
  const { valid } = await formRef.value.validate();

  console.log("Валидация: ", valid)

  if (!valid) {
    console.warn("Форма не прошла валидацию");
    return; // <<< не отправляем, если есть ошибки
  }

  emit("submit");
};

onMounted(() => {
  deviceStore.loadDevices();
});

const deviceOptions = computed(() => deviceStore.devices || []);

defineExpose({
  submit,
});

</script>