import { ref } from "vue";

const snackbar = ref({
  show: false,
  color: "success",
  text: "",
  timeout: 3000,
});

export function useSnackbar() {
  const showSuccess = (text) => {
    snackbar.value = {
      show: true,
      color: "success",
      text,
      timeout: 3000,
    };
  };

  const showError = (text) => {
    snackbar.value = {
      show: true,
      color: "error",
      text,
      timeout: 3000,
    };
  };

  return {
    snackbar,
    showSuccess,
    showError,
  };
}
