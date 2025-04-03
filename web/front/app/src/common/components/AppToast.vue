<template>
  <div style="position: relative;">
    <div class="toast show" v-if="show" data-autohide="false" :style="toastStyles">
      <div class="toast-body">
        <slot />
        <div class="mt-2">
          <button class="btn btn-danger btn-sm me-2" @click="confirm">
            <span class="spinner-border spinner-border-sm" aria-hidden="true" v-if="isLoading"></span>
            <span :class="{ 'visually-hidden': isLoading }" role="status">Да</span>
          </button>
          <button class="btn btn-secondary btn-sm" @click="cancel">Нет</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  toastStyles: {
    type: Object,
    default: {
      position: 'absolute',
      top: `${-10}px`,
      left: `${-180}px`,
      maxWidth: `${180}px`,
      zIndex: 1000,
    },
  },
  isLoading: {
    type: Boolean,
    default: false,
  }
});

const emit = defineEmits(['confirm', 'cancel']);

const confirm = () => {
  emit('confirm');
}

const cancel = () => {
  emit('cancel');
}

</script>