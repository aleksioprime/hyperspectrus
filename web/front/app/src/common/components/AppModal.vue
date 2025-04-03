<template>
  <div class="modal fade" :id="nameModal" tabindex="-1" role="dialog" :aria-labelledby="`${nameModal}Label`"
    data-bs-backdrop="static">
    <div class="modal-dialog" :class="classDialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" :id="`${nameModal}Label`">
            <slot name="header" />
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Закрыть"
            @click="cancel"></button>
        </div>
        <div class="modal-body">
          <slot name="body" />
        </div>
        <div class="modal-footer">
          <slot name="footer"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { watch, onMounted, onBeforeUnmount } from "vue";
import { Modal } from "bootstrap";

const props = defineProps({
  showModal: {
    type: Boolean,
    default: false,
  },
  nameModal: {
    type: String,
    default: 'commonModal',
  },
  classDialog: {
    type: String,
    default: "",
  }
});

let appModal = null;

const emit = defineEmits(['cancel']);

const cancel = () => {
  modalHide();
  emit('cancel');
}

const removeBodyStyles = () => {
  document.body.style.overflow = '';
  document.body.style.paddingRight = '';
  document.body.removeAttribute('cz-shortcut-listen');
}

// Удаление фона компонента во время ошибок
const removeBackdrop = () => {
  const backdrop = document.querySelector('.modal-backdrop');
  if (backdrop) {
    backdrop.remove();
  }
  removeBodyStyles();
}

onBeforeUnmount(() => {
  removeBackdrop();
});

onMounted(() => {
  appModal = new Modal(`#${props.nameModal}`, { backdrop: "static", keyboard: false, focus: false });

  watch(() => props.showModal, (newVal) => {
    if (newVal) {
      appModal.show();
    } else {
      appModal.hide();
      removeBackdrop();
    }
  }, { immediate: true });
});

const modalShow = async () => {
  await appModal.show();
}

const modalHide = async () => {
  await appModal.hide();
}

defineExpose({
  modalShow,
  modalHide,
});
</script>