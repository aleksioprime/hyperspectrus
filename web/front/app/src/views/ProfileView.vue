<template>
  <v-container class="mt-8" max-width="600">
    <v-card class="pa-6" elevation="2" rounded="xl">
      <!-- Фото -->
      <v-row align="center" justify="center" class="mb-1">
        <v-avatar size="96">
          <v-img :src="user.photo || defaultPhoto" alt="Аватар" />
        </v-avatar>
      </v-row>

      <!-- First name -->
      <v-row class="mt-0">
        <v-col class="py-1">
          <div class="text-subtitle-1 font-weight-medium mb-1">Имя</div>
          <v-text-field v-model="editable.first_name" density="compact" />
        </v-col>
      </v-row>

      <!-- Last name -->
      <v-row class="mt-0">
        <v-col class="py-1">
          <div class="text-subtitle-1 font-weight-medium mb-1">Фамилия</div>
          <v-text-field v-model="editable.last_name" density="compact" />
        </v-col>
      </v-row>

      <!-- Email -->
      <v-row class="mt-0">
        <v-col class="py-1">
          <div class="text-subtitle-1 font-weight-medium mb-1">Email</div>
          <v-text-field v-model="editable.email" type="email" density="compact" />
        </v-col>
      </v-row>

      <!-- Организация (только просмотр) -->
      <v-row class="mt-0">
        <v-col class="py-1">
          <div class="text-subtitle-1 font-weight-medium mb-1">Организация</div>
          <v-text-field :model-value="user.organization_id || 'Не указана'" density="compact" disabled />
        </v-col>
      </v-row>

      <!-- Роли (только просмотр) -->
      <v-row class="mt-0">
        <v-col class="py-1">
          <div class="text-subtitle-1 font-weight-medium mb-1">Роли</div>
          <v-chip-group column>
            <v-chip v-for="role in user.roles" :key="role.id" color="primary" variant="tonal" class="me-2">
              {{ role.name }}
            </v-chip>
          </v-chip-group>
        </v-col>
      </v-row>

      <!-- Кнопка сохранить -->
      <v-row justify="center" class="mt-4">
        <v-btn color="primary" @click="saveProfile" :loading="saving">
          <v-icon start>mdi-content-save</v-icon>
          Сохранить
        </v-btn>
      </v-row>
    </v-card>
  </v-container>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import defaultPhoto from "@/assets/img/user-default.png";

const authStore = useAuthStore();
const user = computed(() => authStore.user || {});
const saving = ref(false);

const editable = reactive({
  first_name: user.value.first_name || "",
  last_name: user.value.last_name || "",
  email: user.value.email || "",
});

const saveProfile = async () => {
  saving.value = true;

  const success = await authStore.updateUser({
    id: user.value.id,
    first_name: editable.first_name,
    last_name: editable.last_name,
    email: editable.email,
  });

  saving.value = false;

  if (success) {
    // по желанию: можно показать snackbar или refresh
  }
};
</script>