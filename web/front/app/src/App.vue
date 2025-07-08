<template>
  <v-app :theme="theme.name.value">
    <app-layout>
      <router-view />
    </app-layout>
  </v-app>
</template>

<script setup>
import AppLayout from "@/layouts/AppLayout.vue";

import { watch } from 'vue'
import { useRoute } from 'vue-router'

import { useTheme } from 'vuetify'

const { global: theme } = useTheme()

const route = useRoute()

watch(
  () => route.name,
  () => {
    document.title = route.meta.title
      ? `Hyperspectrus - ${route.meta.title}`
      : 'Hyperspectrus';
  },
  { immediate: true }
)
</script>

<style scoped></style>