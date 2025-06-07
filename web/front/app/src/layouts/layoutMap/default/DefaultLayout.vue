<template>
  <!-- Навигационное меню (боковая панель) -->
  <v-navigation-drawer v-model="drawer" app :temporary="mobile" :width="240">
    <v-list>
      <!-- Заголовок меню -->
      <v-list-item>
        <v-list-item-title class="text-h6">Меню</v-list-item-title>
      </v-list-item>

      <!-- Разделитель -->
      <v-divider />

      <!-- Список пунктов меню -->
      <v-list-item v-for="item in menuItems" :key="item.title" :title="item.title" :prepend-icon="item.icon" link
        :to="{ name: item.to }" @click="drawer = false" />
    </v-list>
  </v-navigation-drawer>

  <!-- Верхняя панель приложения -->
  <v-app-bar app color="primary" dark>
    <!-- Иконка открытия/закрытия боковой панели -->
    <v-app-bar-nav-icon @click="drawer = !drawer" />

    <!-- Заголовок -->
    <v-toolbar-title>
      <router-link :to="{ name: 'home' }" class="text-white text-decoration-none">
        Гиперспектрус
      </router-link>
    </v-toolbar-title>

    <!-- Разделитель пространства между заголовком и кнопками справа -->
    <v-spacer />

    <!-- Кнопка переключения темы (тёмная / светлая) -->
    <v-btn icon @click="toggleTheme" :title="isDark ? 'Светлая тема' : 'Тёмная тема'">
      <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
    </v-btn>

    <!-- Блок авторизации -->
    <template v-if="authStore.isAuthenticated">
      <v-menu>
        <template #activator="{ props }">
          <v-btn v-bind="props" text class="text-none">
            <v-avatar size="32" class="me-2">
              <v-img :src="authStore.user?.photo || defaultPhoto" />
            </v-avatar>
            {{ userFullName }}
            <v-icon end>mdi-menu-down</v-icon>
          </v-btn>
        </template>

        <v-list>
          <v-list-item :to="{ name: 'profile' }" link>
            <v-list-item-title>Профиль</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logout">
            <v-list-item-title>Выйти</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>

    <template v-else>
      <v-btn text :to="{ name: 'login' }">Войти</v-btn>
    </template>
  </v-app-bar>

  <!-- Основной контент страницы -->
  <v-main app>
    <div class="pa-4">
      <!-- Слот для контента, передаваемого в layout -->
      <slot />
    </div>
  </v-main>
</template>

<script setup>
// Импорт реактивных инструментов Vue
import { ref, computed } from 'vue'

// Импорт Vuetify утилит: определение устройства и темы
import { useDisplay, useTheme } from 'vuetify'

// Импорт стора авторизации
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()

// Импорт роутера
import { useRouter } from 'vue-router'
const router = useRouter()

import defaultPhoto from '@/assets/img/user-default.png'

const userFullName = computed(() => {
  const user = authStore.user;
  return user ? `${user.first_name} ${user.last_name}` : "";
});

const drawer = ref(false) // состояние боковой панели
const { mobile } = useDisplay() // определение, мобильное ли устройство

// Элементы бокового меню
const menuItems = [
  { title: 'Главная', icon: 'mdi-home', to: 'home' },
  { title: 'Пациенты', icon: 'mdi-account-multiple', to: 'patient' },
  { title: 'Устройства', icon: 'mdi-camera', to: 'device' },
  { title: 'Хромофоры', icon: 'mdi-molecule', to: 'chromophore' },
  { title: 'Настройки', icon: 'mdi-cog', to: 'config' },
]

// Работа с глобальной темой
const { global: theme } = useTheme()
const isDark = computed(() => theme.name.value === 'dark') // текущая тема — тёмная?

// Переключение темы: dark <-> light
function toggleTheme() {
  theme.name.value = isDark.value ? 'light' : 'dark'
}

// Выход пользователя и переход на страницу логина
async function logout() {
  await authStore.logout()
  router.push({ name: 'login' }) // редирект на login после logout
}
</script>

<style>
/* Стилизация основной области приложения */
</style>