<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="pa-4" elevation="10" rounded="xl">
          <v-card-title class="text-center text-h5 font-weight-bold">
            HyperspectRUS
          </v-card-title>

          <v-card-subtitle class="text-center mb-4">
            Войдите в свой аккаунт
          </v-card-subtitle>

          <!-- Сообщение об ошибке сервера -->
          <v-alert v-if="serverErrorMessage" type="error" variant="tonal" class="mb-4" border="start">
            {{ serverErrorMessage }}
          </v-alert>

          <v-form @submit.prevent="handleLogin" ref="form">
            <v-text-field v-model="username" label="Пользователь" type="text" prepend-inner-icon="mdi-account"
              :error="!!validations.username.error" :error-messages="validations.username.error" autocomplete="username"
              autofocus required density="comfortable" variant="outlined" class="mb-1" />
            <v-text-field v-model="password" label="Пароль" type="password" prepend-inner-icon="mdi-lock"
              :error="!!validations.password.error" :error-messages="validations.password.error"
              autocomplete="current-password" required density="comfortable" variant="outlined" class="mb-2" />
            <v-btn type="submit" color="primary" size="large" block elevation="2" :loading="loading">
              Войти
            </v-btn>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores';

import { validateFields, clearValidationErrors } from '@/common/validator';
import jwtService from "@/services/jwt/jwt.service";

const router = useRouter()
const authStore = useAuthStore()

// Состояния
const username = ref('')
const password = ref('')
const loading = ref(false)
const serverErrorMessage = ref(null)

const setEmptyValidations = () => ({
  username: {
    error: '',
    rules: ['required']
  },
  password: {
    error: '',
    rules: ['required']
  }
})

const validations = ref(setEmptyValidations())

// Очистка ошибок при вводе
watch(username, () => {
  serverErrorMessage.value = null
  clearValidationErrors(validations.value, 'username')
})

watch(password, () => {
  serverErrorMessage.value = null
  clearValidationErrors(validations.value, 'password')
})

// Обработка входа
async function handleLogin() {
  if (!validateFields(
    { username: username.value, password: password.value },
    validations.value
  )) return

  loading.value = true
  serverErrorMessage.value = null

  const credentials = {
    username: username.value,
    password: password.value,
  }

  const responseMessage = await authStore.login(credentials);
  loading.value = false;

  if (responseMessage !== 'success') {
    serverErrorMessage.value = responseMessage;
    return
  }

  await authStore.getMe();
  await router.push({ name: "home" });
}

onMounted(async () => {
  const accessToken = jwtService.getAccessToken();

  if (accessToken && authStore.isAuthenticated) {
    router.push({ name: "home" });
  }
})
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
  background: linear-gradient(to right, #6a11cb, #2575fc);
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>