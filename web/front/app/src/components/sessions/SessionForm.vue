<template>
  <v-form @submit.prevent="submit" ref="formRef">
    <v-text-field v-model="form.date" label="Дата и время сеанса" type="datetime-local"
      :rules="[v => !!v || 'Обязательное поле']" required />
    <v-textarea v-model="form.notes" label="Заметки" rows="2" />
  </v-form>
</template>

<script setup>
import { ref, watch, reactive } from "vue";

const props = defineProps({ modelValue: Object });
const emit = defineEmits(["submit", "update:modelValue"]);

const form = reactive({
  date: "",
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

const submit = () => {
  formRef.value?.validate();
  emit("submit");
};
</script>