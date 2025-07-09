<template>
  <v-form ref="formRef" @submit.prevent="onSubmit" >
    <v-text-field v-model="form.full_name" label="ФИО" :rules="[rules.required]" required />
    <v-text-field v-model="form.birth_date" label="Дата рождения" type="date" :rules="[rules.required]"
      required />
    <v-textarea v-model="form.notes" label="Заметки" auto-grow />
  </v-form>
</template>

<script setup>
import { ref, watch, reactive } from "vue";
import rules from "@/common/helpers/rules";

const props = defineProps({
  modelValue: Object,
});
const emit = defineEmits(["update:modelValue"]);

const form = reactive({
  full_name: "",
  birth_date: "",
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

defineExpose({ submit: onSubmit });
</script>