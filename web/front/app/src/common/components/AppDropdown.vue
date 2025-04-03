<template>
  <div class="select-field">
    <label v-if="label" :for="name" class="form-label">{{ label }}</label>
    <div class="dropdown">
      <button class="btn btn-light dropdown-toggle" type="button" id="dropdownMenuModule" data-bs-toggle="dropdown"
        aria-expanded="false" :disabled="disabled">
        <slot name="selected" :selected="displayValue">
          <span v-if="displayValue">{{ displayValue[props.labelField] }}</span>
          <span v-else>{{ placeholder }}</span>
        </slot>
      </button>
      <ul class="dropdown-menu" aria-labelledby="dropdownMenuModule">
        <li @click="changingNullData">
          <a class="dropdown-item" :class="{ 'active': !selectedValue }" href="javascript:void(0)">
            {{ placeholder }}
          </a>
        </li>
        <li v-for="option in options" :key="option[valueField]" @click="changingData(option)">
          <a class="dropdown-item" :class="{ 'active': option[valueField] == selectedValue }" href="javascript:void(0)">
            <slot name="option" :option="option">
              {{ option[labelField] }}
            </slot>
          </a>
        </li>
      </ul>
    </div>
    <span v-if="showError" class="select-field__text" v-html="errorText"></span>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: [Object, String, Number, null],
    default: null
  },
  options: {
    type: Array,
    default: () => []
  },
  labelField: {
    type: String,
    default: 'name',
  },
  valueField: {
    type: String,
    default: 'id'
  },
  title: {
    type: String,
    default: '',
  },
  name: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: null
  },
  errorText: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Все'
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  isNumber: {
    type: Boolean,
    default: false,
  }
});

const emit = defineEmits(['update:modelValue', 'changing']);

// Вычисляемое свойство для определения, является ли modelValue объектом
const isObjectValue = computed(() => {
  if (props.isNumber) {
    return false
  } else {
    return typeof props.modelValue === 'object';
  }
});

const selectedOption = ref(null)

// Локальное состояние для текущего выбранного значения в select элементе
const selectedValue = ref(isObjectValue.value ?
  (props.modelValue ? props.modelValue[props.valueField] : '') :
  (props.modelValue ? props.modelValue : '')
);

const displayValue = computed(() => {
  selectedOption.value = props.options.find(option => option[props.valueField] == selectedValue.value);
  if (selectedOption.value) {
    return selectedOption.value
  }
});

// Обработчик изменения значения в select элементе
const changingData = (newValue) => {
  selectedOption.value = props.options.find(option => option[props.valueField] == newValue[props.valueField]);
  if (isObjectValue.value) {
    emit('update:modelValue', selectedOption.value);
  } else {
    emit('update:modelValue', selectedOption.value[props.valueField]);
  }
  emit('changing', { [props.name]: selectedOption.value[props.valueField] });
};

const changingNullData = () => {
  selectedOption.value = null;
  emit('update:modelValue', null);
  emit('changing', { [props.name]: null });
}

// Наблюдатель за изменениями modelValue пропса
watch(() => props.modelValue, (newValue) => {
  selectedValue.value = newValue
    ? isObjectValue.value
      ? newValue[props.valueField]
      : newValue
    : '';
});

const showError = computed(() => {
  return !!props.errorText
})
</script>

<style scoped>

.dropdown-toggle {
  width: 100%;
  text-align: left;
  padding-right: 20px;
}
.dropdown-toggle::after {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
}
.dropdown-menu {
  max-height: 400px;
  overflow-y: scroll;
}

.dropdown-toggle::after {
  margin-left: 10px;
}
</style>