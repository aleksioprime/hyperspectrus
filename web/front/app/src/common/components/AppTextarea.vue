<template>
  <div class="text-field">
    <textarea ref="textarea" :value="modelValue" :name="props.name" class="form-control " :rows="props.rows"
      :class="{ 'text-field__input--error': showError }" :placeholder="props.placeholder" :required="props.required"
      @input="$emit('update:modelValue', $event.target.value)" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ' '
  },
  name: {
    type: String,
    required: true
  },
  placeholder: {
    type: String,
    default: ''
  },
  errorText: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  rows: {
    type: Number,
    default: 2
  },
})

defineEmits(['update:modelValue'])

const showError = computed(() => {
  return !props.modelValue && !!props.errorText;
})

const textarea = ref(null);
// Автоподстройка высоты
const adjustTextareaHeight = () => {
  const el = textarea.value;

  if (!el) {
    return;
  }

  const lineHeight = parseFloat(getComputedStyle(el).lineHeight);
  const minHeight = lineHeight * props.rows * 2;

  el.style.height = 'auto';
  el.style.height = `${Math.max(el.scrollHeight, minHeight)}px`;

};

// Подстройка высоты после монтирования
onMounted(() => {
  adjustTextareaHeight();
});

</script>