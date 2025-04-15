<template>
  <v-form @submit.prevent="submit" ref="formRef">
    <v-text-field
      v-model="form.full_name"
      label="ФИО"
      :rules="[v => !!v || 'Обязательное поле']"
      required
    />
    <v-text-field
      v-model="form.birth_date"
      label="Дата рождения"
      type="date"
      :rules="[v => !!v || 'Обязательное поле']"
      required
    />
    <v-textarea
      v-model="form.notes"
      label="Заметки"
    />
  </v-form>
</template>

<script setup>
import { ref, watch, reactive } from "vue";

const props = defineProps({
  modelValue: Object,
});
const emit = defineEmits(["submit", "update:modelValue"]);

const form = reactive({
  full_name: "",
  birth_date: "",
  notes: "",
});

const formRef = ref();

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    Object.assign(form, newVal);
  }
}, { immediate: true });

watch(form, () => {
  emit("update:modelValue", { ...form });
}, { deep: true });

const submit = () => {
  formRef.value?.validate();
  emit("submit");
};
</script>
