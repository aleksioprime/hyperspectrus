<!--
  Этот компонент представляет собой кнопку, которая может содержать произвольный контент.
  Пропсы:
    - type: тип кнопки (например, 'button', 'submit', 'reset').
    - class: CSS-классы для стилизации кнопки.
  Функционал:
    - Предоставляет базовую кнопку с поддержкой передачи произвольного контента через слот.
    - Позволяет задавать тип кнопки и CSS-классы для кастомизации внешнего вида и поведения.
-->

<template>
  <button :class="class" :type="type">
    <span class="spinner-border spinner-border-sm me-2" aria-hidden="true" v-if="isLoading"></span>
    <span role="status">
      <slot />
    </span>
  </button>
</template>

<script setup>

defineProps({
  type: {
    type: String,
    default: 'button'
  },
  class: {
    type: String,
    default: 'btn-light'
  },
  isLoading: {
    type: Boolean,
    default: false,
  }
})

</script>