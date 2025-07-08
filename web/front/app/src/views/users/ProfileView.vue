<template>
  <h1 class="text-h5 mb-4">Профиль пользователя</h1>

  <v-row no-gutters>
    <!-- Аватар и загрузка фото -->
    <v-col cols="12" md="3" class="d-flex flex-column align-start">
      <div class="relative mb-4 mb-md-0">
        <v-avatar size="200" class="elevation-3" rounded="xl" style="border: 2px solid #fff;">
          <v-img :src="srcPhotoUrl" cover />
        </v-avatar>

        <input ref="fileInput" type="file" accept="image/*" class="d-none" @change="onPhotoChange">

        <!-- Кнопки загрузки и очистки -->
        <div v-if="!previewUrl && !photoWasCleared" class="d-flex flex-column align-center mt-6" style="gap: 16px">
          <v-btn color="primary" variant="tonal" prepend-icon="mdi-camera" size="small" @click="onPhotoClick">
            Загрузить фото
          </v-btn>
          <v-btn color="grey" variant="tonal" prepend-icon="mdi-delete" size="small" @click="clearSelectedPhoto">
            Очистить
          </v-btn>
        </div>

        <!-- Кнопки подтверждения и отмены -->
        <div v-if="previewUrl || photoWasCleared" class="d-flex justify-center mt-3" style="gap: 16px">
          <v-btn icon="mdi-check" color="success" size="small" class="rounded-circle" @click="confirmPhoto" />
          <v-btn icon="mdi-close" color="error" size="small" class="rounded-circle" @click="cancelPhoto" />
        </div>

      </div>
    </v-col>

    <!-- Форма профиля -->
    <v-col cols="12" md="9">
      <v-row class="mb-4" v-if="isSuperuser">
        <v-col cols="12">
          <v-chip v-if="isSuperuser" color="amber" size="large" class="me-2" label style="font-weight: bold">
            <v-icon start size="20">mdi-crown</v-icon>
            Суперпользователь
          </v-chip>
        </v-col>
      </v-row>
      <v-form @submit.prevent="saveProfile" v-model="valid" ref="formRef">
        <v-text-field v-model="form.username" label="Логин" :rules="usernameRules" />
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.first_name" label="Имя" :rules="nameRules" />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.last_name" label="Фамилия" :rules="nameRules" />
          </v-col>
        </v-row>
        <v-text-field v-model="form.email" label="Email" :rules="emailRules" type="email" />
        <v-row class="mt-0">
          <v-col class="py-1">
            <div class="text-subtitle-1 font-weight-medium mb-1">Организация</div>
            <v-text-field :model-value="user.organization?.name || 'Не указана'" density="compact" readonly />
          </v-col>
        </v-row>
        <div class="text-subtitle-1 font-weight-medium mb-1">Роли</div>
        <v-chip-group column>
          <v-chip v-for="role in user.roles" :key="role.id" color="primary" variant="tonal" class="me-2" :ripple="false"
            style="pointer-events: none; cursor: default;">
            {{ role.name }}
          </v-chip>
        </v-chip-group>
        <div class="mt-4">
          <v-btn color="primary" type="submit" :loading="loading" :disabled="!valid || !isChanged">Сохранить</v-btn>
          <v-btn color="secondary" type="button" class="ms-2" @click="openResetPasswordDialog(user)">Изменить
            пароль</v-btn>
        </div>
      </v-form>
    </v-col>
  </v-row>

  <!-- Модальное окно сброса пароля -->
  <v-dialog v-model="modalDialogResetPassword.visible" max-width="400px">
    <v-card>
      <v-card-title>Сбросить пароль?</v-card-title>
      <v-card-text>
        <div v-if="modalDialogResetPassword.user">
          Задайте новый пароль для пользователя
          <strong>{{ modalDialogResetPassword.user.last_name }} {{ modalDialogResetPassword.user.first_name }}</strong>:
        </div>
        <PasswordForm ref="passwordFormRef" v-model="modalDialogResetPassword.form" />
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="modalDialogResetPassword.visible = false">Отмена</v-btn>
        <v-btn color="primary" @click="confirmResetPassword">Сбросить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const defaultPhoto = "https://ui-avatars.com/api/?background=ccc&color=444&size=128&name=User"
import rules from "@/common/helpers/rules";
import { cacheBustUrl } from "@/common/helpers/cacheBust";

import PasswordForm from "@/components/users/PasswordForm.vue";

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();

import { useUserStore } from "@/stores/user";
const userStore = useUserStore();

const user = reactive(authStore.user)

const isSuperuser = computed(() => user.is_superuser);

// --- РЕДАКТИРОВАНИЕ ПОЛЕЙ ---

const form = reactive({
  first_name: user.first_name,
  last_name: user.last_name,
  email: user.email,
  username: user.username,
})

const loading = ref(false)
const valid = ref(true)
const formRef = ref(null)

const usernameRules = [rules.required, rules.username, rules.minLength(3), rules.maxLength(20)];
const nameRules = [rules.required, rules.minLength(2), rules.maxLength(30), rules.onlyLetters];
const emailRules = [rules.required, rules.email];

const saveProfile = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  loading.value = true
  await userStore.updateUser(user.id, form);
  initialForm.value = { ...form }
  loading.value = false
}

// --- ЗАГРУЗКА ФОТОГРАФИИ ---

const photoWasCleared = ref(false)

const photoUrl = ref(user.photo)       // Текущий URL аватарки (подтверждённый)
const previewUrl = ref(null)           // Для предпросмотра после выбора файла
const fileInput = ref(null)
const tempPhotoFile = ref(null)

// Открытие окна выбора локального изображения
const onPhotoClick = () => {
  fileInput.value?.click()
}

const clearSelectedPhoto = () => {
  previewUrl.value = null;
  tempPhotoFile.value = null;
  photoWasCleared.value = true;
}

//
const onPhotoChange = e => {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = ev => {
      previewUrl.value = ev.target.result
      tempPhotoFile.value = file
    }
    reader.readAsDataURL(file)
  }
}

// Подтверждение загрузки выбранного изображения
const confirmPhoto = async () => {
  loading.value = true;
  if (photoWasCleared.value) {
    const result = await userStore.deletePhoto(user.id);
    if (result) {
      photoUrl.value = null;
      if (authStore.user) authStore.user.photo = null;
    }
    cancelPhoto();
    loading.value = false;
    return;
  }

  if (tempPhotoFile.value) {
    const formData = new FormData();
    formData.append('photo', tempPhotoFile.value);

    const result = await userStore.uploadPhoto(user.id, formData);
    if (result && result.photo) {
      photoUrl.value = result.photo + "?v=" + Date.now();
      if (authStore.user) authStore.user.photo = result.photo;
    }
    cancelPhoto();
    loading.value = false;
    return;
  }

  cancelPhoto();
  loading.value = false;
}

// Отмена загрузки выбранного изображения
const cancelPhoto = () => {
  previewUrl.value = null;
  tempPhotoFile.value = null;
  photoWasCleared.value = false;
  loading.value = false;
  if (fileInput.value) fileInput.value.value = '';
}

const srcPhotoUrl = computed(() => {
  if (previewUrl.value) return previewUrl.value;
  if (photoWasCleared.value) return defaultPhoto;
  if (photoUrl.value) return cacheBustUrl(photoUrl.value);
  return defaultPhoto;
});

// --- СЛЕЖЕНИЕ ЗА ИЗМЕНЕНИЕМ ДАННЫХ ---

const initialForm = ref({ ...form })

const isChanged = computed(() => {
  return (
    form.first_name !== initialForm.value.first_name ||
    form.last_name !== initialForm.value.last_name ||
    form.email !== initialForm.value.email ||
    form.username !== initialForm.value.username
  )
})

// --- МОДАЛЬНОЕ ОКНО СБРОСА ПАРОЛЯ ---

// Объект модального окна
const modalDialogResetPassword = ref({
  visible: false,
  user: null,
  form: { password: '', repeatPassword: '' }
});

// Вызов модального окна сброса пароля
const openResetPasswordDialog = (user) => {
  modalDialogResetPassword.value = {
    visible: true,
    user: user,
    form: { password: '', repeatPassword: '' }
  };
};

// Подтверждение сброса пароля
const confirmResetPassword = async () => {
  const { form, user } = modalDialogResetPassword.value;
  if (!form.password || form.password !== form.repeatPassword) return;
  await userStore.resetPassword(user.id, form);
  modalDialogResetPassword.value.visible = false;
};
</script>


<style scoped>
.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.end-0 {
  right: 0;
}

.bottom-0 {
  bottom: 0;
}

.d-none {
  display: none;
}
</style>