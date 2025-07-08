<template>
  <v-form ref="formRef" @submit.prevent="onSubmit">
    <v-text-field v-model="form.name" label="Название" :rules="nameRules" required clearable />
    <v-textarea v-model="form.description" label="Описание" clearable auto-grow />
  </v-form>
</template>

<script setup>
import { ref, reactive, watch } from "vue";
import rules from "@/common/helpers/rules";

const props = defineProps({
  modelValue: { type: Object, required: false, default: () => ({}) },
});
const emit = defineEmits(["update:modelValue"]);

// Локальное состояние формы
const form = reactive({
  name: "",
  description: "",
});

// Валидация полей
const nameRules = [rules.required, rules.minLength(2), rules.maxLength(64)];

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