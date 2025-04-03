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
        @click="drawer = false" />
    </v-list>
  </v-navigation-drawer>

  <!-- Верхняя панель приложения -->
  <v-app-bar app color="primary" dark>
    <!-- Иконка открытия/закрытия боковой панели -->
    <v-app-bar-nav-icon @click="drawer = !drawer" />

    <!-- Заголовок -->
    <v-toolbar-title>Моё приложение</v-toolbar-title>

    <!-- Разделитель пространства между заголовком и кнопками справа -->
    <v-spacer />

    <!-- Кнопка переключения темы (тёмная / светлая) -->
    <v-btn icon @click="toggleTheme" :title="isDark ? 'Светлая тема' : 'Тёмная тема'">
      <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
    </v-btn>

    <!-- Блок авторизации -->
    <template v-if="authStore.isAuthenticated">
      <!-- Кнопка выхода -->
      <v-btn text @click="logout">Выйти</v-btn>
    </template>
    <template v-else>
      <!-- Кнопка входа (редирект на страницу логина) -->
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

const drawer = ref(false) // состояние боковой панели
const { mobile } = useDisplay() // определение, мобильное ли устройство

// Элементы бокового меню
const menuItems = [
  { title: 'Главная', icon: 'mdi-home' },
  { title: 'Профиль', icon: 'mdi-account' },
  { title: 'Настройки', icon: 'mdi-cog' },
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