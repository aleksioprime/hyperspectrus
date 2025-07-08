<template>
  <v-form ref="formRef" v-model="isFormValid" @submit.prevent="onSubmit">
    <v-text-field v-model="form.password" label="Новый пароль" :type="'password'" :rules="passwordRules" required
      class="mt-4" />
    <v-text-field v-model="form.repeatPassword" label="Повторите пароль" :type="'password'"
      :rules="repeatPasswordRules(form.password)" required class="mt-2" />
  </v-form>
</template>

<script setup>
import { ref, reactive, watch } from "vue";
import rules from "@/common/helpers/rules";

const props = defineProps({
  modelValue: { type: Object, required: false, default: () => ({}) },
});
const emit = defineEmits(["update:modelValue", "submit"]);

// Локальное состояние формы
const form = reactive({
  password: "",
  repeatPassword: "",
});

const isFormValid = ref(true);

// Валидация полей
const passwordRules = [rules.required, rules.minLength(6)];
const repeatPasswordRules = (password) => [rules.required, rules.sameAs(password, "Пароли не совпадают")];

// Синхронизация изменения внешнего modelValue с внутренним
watch(() => props.modelValue, (newVal) => {
  if (newVal) Object.assign(form, newVal);
}, { immediate: true });

// Синхронизация изменения внутренего modelValue с внешним
watch(form, () => {
  emit("update:modelValue", { ...form });
}, { deep: true });

// Отправка формы
const formRef = ref();

const onSubmit = async () => {
  const { valid } = await formRef.value?.validate();
  return valid
};

defineExpose({ submit: onSubmit });
</script>