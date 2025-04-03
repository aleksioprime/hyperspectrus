<template>
  <div>
    <label v-if="label" :for="name" class="form-label">{{ label }}</label>
    <input :value="modelValue" :type="type" :name="name" :id="name" class="form-control" :placeholder="placeholder" :required="required"
      @input="changingData" :autocomplete="`new-${name}`" :size="size" :disabled="disabled"/>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: null
  },
  label: {
    type: String,
    default: null
  },
  name: {
    type: String,
    required: true,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
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
  size: {
    type: String,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'changing'])

// Вызывается при изменении данных
const changingData = (event) => {
  const newValue = event.target.value;
  emit('update:modelValue', newValue);
}

watch(() => props.modelValue, (newValue) => {
  const newValueObject = { [props.name]: newValue }
  emit('changing', newValueObject);
});

const showError = computed(() => {
  return !!props.errorText
})
</script>

<style scoped>

</style>