<template>
  <h1 class="text-h5 mb-4">Пользователи</h1>

  <div class="d-flex align-top justify-space-between">
    <v-btn v-if="canEdit" color="primary" class="my-2" @click="openCreateDialog">
      <v-icon start>mdi-plus</v-icon>
      Добавить
    </v-btn>
    <v-select v-model="selectedOrganization" :items="organizations" item-value="id" item-title="name"
      label="Организация" clearable style="max-width: 300px" />
  </div>

  <v-list class="my-3">
    <v-list-item v-for="(user, index) in users" :key="user.id" :class="{ 'admin-list-item': user.is_superuser }">
      <!-- Фото -->
      <template #prepend>
        <v-avatar size="56">
          <v-img :src="cacheBustUrl(user.photo) || defaultPhoto" alt="Фото пользователя" cover />
        </v-avatar>
      </template>

      <!-- Данные -->
      <v-list-item-title>
        <b>{{ user.first_name || "<First Name>" }} {{ user.last_name || "<Last Name>" }}
              <v-icon v-if="user.is_superuser" color="orange darken-2" size="18" class="ms-1" title="Администратор"
                style="vertical-align: middle;">mdi-shield-account</v-icon>
        </b>
      </v-list-item-title>
      <v-list-item-subtitle>
        {{ user.username }} ({{ user.email }})
      </v-list-item-subtitle>

      <div class="mt-2" v-if="user.roles && user.roles.length">
        <v-chip v-for="role in user.roles" :key="role.id || role.name" color="primary" variant="tonal" size="small"
          class="me-2" label>
          {{ role.display_name }}
        </v-chip>
      </div>

      <!-- Кнопки редактирования или удаления -->
      <template #append>
        <v-btn icon @click="openEditDialog(user)">
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-btn icon @click="deleteUser(user)" v-if="authStore.user?.id != user?.id" class="ms-2">
          <v-icon color="red">mdi-delete</v-icon>
        </v-btn>
        <v-btn icon @click="openResetPasswordDialog(user)" class="ms-2" title="Сбросить пароль">
          <v-icon color="blue">mdi-lock-reset</v-icon>
        </v-btn>
        <v-btn icon class="ms-2" @click="openPhotoDialog(user)" title="Изменить фото">
          <v-icon color="primary">mdi-camera</v-icon>
        </v-btn>
      </template>
    </v-list-item>
  </v-list>

  <div ref="infiniteScrollTarget" />

  <div class="text-center my-4" v-if="loading">
    <v-progress-circular indeterminate color="primary" />
  </div>

  <div class="text-center my-4" v-if="!loading && !hasNextPage && users.length">
    <v-alert type="info" density="compact" border="start" variant="tonal">
      Все пользователи загружены
    </v-alert>
  </div>

  <!-- Модальное окно добавления/редактирования пользователя -->
  <v-dialog v-model="modalDialogEdit.visible" max-width="500px" persistent>
    <v-card>
      <v-card-title>
        {{ modalDialogEdit.editing ? 'Редактировать пользователя' : 'Новый пользователь' }}
      </v-card-title>
      <v-card-text>
        <UserForm ref="userFormRef" v-model="modalDialogEdit.form" :is-create="!modalDialogEdit.editing" />
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="modalDialogEdit.visible = false">Отмена</v-btn>
        <v-btn color="primary" @click="submitDialog">
          {{ modalDialogEdit.editing ? 'Сохранить' : 'Создать' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Модальное окно удаления пользователя -->
  <v-dialog v-model="modalDialogDelete.visible" max-width="400px">
    <v-card>
      <v-card-title>Удалить пользователя?</v-card-title>
      <v-card-text>
        Вы уверены, что хотите удалить пользователя <strong>
          {{ modalDialogDelete.user?.last_name }} {{ modalDialogDelete.user?.first_name }}</strong>?
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="modalDialogDelete.visible = false">Отмена</v-btn>
        <v-btn color="red" @click="confirmDeleteUser">Удалить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

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

  <!-- Диалог для загрузки/смены фото пользователя -->
  <v-dialog v-model="modalDialogPhoto.visible" max-width="400px">
    <v-card>
      <v-card-title>Загрузка фото</v-card-title>
      <v-card-text>
        <div class="d-flex align-center">
          <v-avatar size="120" class="elevation-3 me-2">
            <v-img :src="photoWasCleared ? defaultPhoto : (previewUrl || modalDialogPhoto.user?.photo || defaultPhoto)"
              cover />
          </v-avatar>
          <input ref="fileInput" type="file" accept="image/*" class="d-none" @change="onPhotoChange">
          <div class="d-flex flex-column align-center w-100" style="gap: 8px">
            <v-btn color="primary" @click="onPhotoClick">Изменить</v-btn>
            <v-btn color="grey" @click="clearSelectedPhoto"
              :disabled="!previewUrl && !modalDialogPhoto.user?.photo">Очистить</v-btn>
          </div>
        </div>
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn color="success" @click="confirmPhoto" :disabled="!previewUrl && !photoWasCleared">Сохранить</v-btn>
        <v-btn @click="cancelPhoto">Отмена</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useIntersectionObserver } from "@vueuse/core";
import logger from '@/common/helpers/logger';

import UserForm from "@/components/users/UserForm.vue";
import PasswordForm from "@/components/users/PasswordForm.vue";
import defaultPhoto from '@/assets/img/user-default.png'
import { cacheBustUrl } from "@/common/helpers/cacheBust";

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();

import { useUserStore } from "@/stores/user";
const userStore = useUserStore();
const users = ref([]);

import { useOrganizationStore } from "@/stores/organization";
const organizationStore = useOrganizationStore();
const organizations = ref([]);

// --- СПИСОК ПОЛЬЗОВАТЕЛЕЙ ---

// Переменные пагинированного списка
const page = ref(0);
const limit = 20;
const total = ref(0);
const hasNextPage = ref(true);

// Переменная процесса загрузки
const loading = ref(false);

// Загрузка пагинированного списка пользователя
const fetchUsers = async (reset = false) => {
  // Если уже идёт загрузка или больше нет данных — ничего не делаем
  if (loading.value) return;
  // Ставим флаг загрузки, чтобы не вызвать функцию повторно
  loading.value = true;

  // Если изменился фильтр или нужно перезагрузить весь список
  if (reset) {
    users.value = [];
    page.value = 0;
    hasNextPage.value = true;
  }

  // Формируем параметры запроса для API
  const params = {
    offset: page.value,
    limit,
  };

  // Если выбраны фильтры, то они добавляются в параметры
  if (selectedOrganization.value) {
    params.organization_id = selectedOrganization.value;
  }

  // Запрос к API с передачей параметров
  const data = await userStore.loadUsers({ params: params });

  // Если данные получены:
  if (data) {
    users.value.push(...data.items);
    total.value = data.total;
    hasNextPage.value = data.has_next;
    page.value += 1;
  }

  loading.value = false; // Снимаем флаг загрузки
};

// Элемент страницы, который активирует подзагрузку списка
const infiniteScrollTarget = ref(null);

// Хук, который следит, попал ли элемент подзагрузки списка в поле видимости
useIntersectionObserver(
  infiniteScrollTarget,
  ([{ isIntersecting }]) => {
    if (isIntersecting) {
      fetchUsers();
    }
  },
  { threshold: 1.0 }
);

// --- ДОБАВЛЕНИЕ/РЕДАКТИРОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ ---

// Метка возможности редактирования
const canEdit = computed(() =>
  authStore.user?.is_superuser ||
  authStore.user?.roles?.some(role =>
    ["admin"].includes(role.name)
  )
);

// Объект модального окна
const modalDialogEdit = ref({
  visible: false,
  editing: false,
  form: {},
});

// Открытие модального окна для создания пользователя
const openCreateDialog = () => {
  modalDialogEdit.value = {
    visible: true,
    editing: false,
    form: {
      id: null,
      first_name: "",
      last_name: "",
      email: "",
      username: "",
      password: "",
      repeat_password: "",
      roles: [],
      organization: '',
      is_superuser: false,
    },
  };
};

// Открытие модального окна для редактирования пользователя
const openEditDialog = (user) => {
  modalDialogEdit.value = {
    visible: true,
    editing: true,
    form: {
      id: user.id,
      username: user.username,
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      roles: user.roles,
      organization: user.organization,
      is_superuser: user.is_superuser,
    },
  };
};

// Подготовка данных формы для запроса редактирования пользователя
const getUserUpdatePayload = (form) => {
  return {
    id: form.id,
    first_name: form.first_name,
    last_name: form.last_name,
    email: form.email,
    username: form.username,
    roles: form.roles,
    organization_id: form.organization,
    is_superuser: form.is_superuser,
  }
}

// Подготовка данных формы для запроса создания пользователя
const getUserCreatePayload = (form) => {
  return {
    first_name: form.first_name,
    last_name: form.last_name,
    email: form.email,
    username: form.username,
    password: form.password,
    roles: form.roles,
    organization_id: form.organization,
    is_superuser: form.is_superuser,
  }
}

// Подтверждение создания/редактирования пользователя
const userFormRef = ref();

const submitDialog = async () => {
  const valid = await userFormRef.value?.submit();
  if (!valid) return;

  const { form, editing } = modalDialogEdit.value;

  if (editing) {
    const result = await userStore.updateUser(form.id, getUserUpdatePayload(form));
    if (!result) return;
    const index = users.value.findIndex(p => p.id === form.id);
    if (index !== -1) users.value[index] = { ...users.value[index], ...result };
  } else {
    const newUser = await userStore.createUser(getUserCreatePayload(form));
    if (!newUser) return;
    users.value.push(newUser);
    users.value.sort((a, b) => {
      const aName = (a.last_name || a.first_name || '').toLowerCase();
      const bName = (b.last_name || b.first_name || '').toLowerCase();
      return aName.localeCompare(bName);
    });
  }

  modalDialogEdit.value.visible = false;
};

// --- УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ---

// Объект модального окна
const modalDialogDelete = ref({
  visible: false,
  user: null,
});

// Вызов модального окна удаления
const deleteUser = (user) => {
  modalDialogDelete.value = { visible: true, user };
};

// Подтверждение удаления в модальном окне
const confirmDeleteUser = async () => {
  const user = modalDialogDelete.value.user;

  const result = await userStore.deleteUser(user.id);
  if (!result) return;

  users.value = users.value.filter((p) => p.id !== user.id);
  modalDialogDelete.value.visible = false;
};

// --- СБРОС ПАРОЛЯ ---
const passwordFormRef = ref();

// Объект модального окна
const modalDialogResetPassword = ref({
  visible: false,
  user: null,
  form: {
    password: '',
    repeatPassword: '',
  }
});

// Вызов модального окна сброса пароля
const openResetPasswordDialog = (user) => {
  modalDialogResetPassword.value = {
    visible: true,
    user,
    form: {
      password: '',
      repeatPassword: '',
    }
  };
};

// Подтверждение сброса пароля
const confirmResetPassword = async () => {
  const valid = await passwordFormRef.value?.submit();
  if (!valid) return;

  const { form, user } = modalDialogResetPassword.value;

  const result = await userStore.resetPassword(user.id, form);
  if (!result) return;

  modalDialogResetPassword.value.visible = false;
};

// --- ЗАГРУЗКА ФОТОГРАФИИ ПОЛЬЗОВАТЕЛЯ ---

const photoWasCleared = ref(false);

// --- Переменные для загрузки фото ---
const modalDialogPhoto = ref({
  visible: false,
  user: null,
});
const previewUrl = ref(null)
const fileInput = ref(null)
const tempPhotoFile = ref(null)

// Открытие модального окна для загрузки фото
const openPhotoDialog = (user) => {
  modalDialogPhoto.value = {
    visible: true,
    user,
  };
  previewUrl.value = null;
  tempPhotoFile.value = null;
  photoWasCleared.value = false;
};

// Открытие окна выбора локального изображения
const onPhotoClick = () => {
  fileInput.value?.click();
};

// Очистка поля от изображения
const clearSelectedPhoto = () => {
  previewUrl.value = null;
  tempPhotoFile.value = null;
  photoWasCleared.value = true;
};

// Обработка выбранного изображения
const onPhotoChange = e => {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = ev => {
      previewUrl.value = ev.target.result;
      tempPhotoFile.value = file;
      photoWasCleared.value = false;
    };
    reader.readAsDataURL(file);
  }
};

// Подтвердить загрузку изображения
const confirmPhoto = async () => {
  const user = modalDialogPhoto.value.user;
  if (!user) return;

  const formData = new FormData();

  if (photoWasCleared.value) {
    const result = await userStore.deletePhoto(user.id);
    if (!result) return;

    const index = users.value.findIndex(u => u.id == user.id);
    if (index !== -1) users.value[index].photo = null;

    cancelPhoto();
    return;
  }

  if (tempPhotoFile.value) {
    const formData = new FormData();
    formData.append('photo', tempPhotoFile.value);

    const result = await userStore.uploadPhoto(user.id, formData);
    if (!result) return;

    const index = users.value.findIndex(u => u.id == user.id);
    if (index !== -1) users.value[index].photo = result.photo + '?v=' + Date.now();

    cancelPhoto();
    return;
  }

  cancelPhoto()
};

// Отмена загрузки
const cancelPhoto = () => {
  previewUrl.value = null;
  tempPhotoFile.value = null;
  photoWasCleared.value = false;
  if (fileInput.value) fileInput.value.value = '';
  modalDialogPhoto.value.visible = false;
};

// --- ФИЛЬТР ПО ОРГАНИЗАЦИИ ---
const selectedOrganization = ref(null);

onMounted(async () => {
  organizations.value = await organizationStore.loadOrganizations?.() || [];
});

watch(selectedOrganization, () => {
  fetchUsers(true);
});

</script>