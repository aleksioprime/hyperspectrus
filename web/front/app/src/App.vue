<template>
  <v-app :theme="theme.name.value">
    <app-layout>
      <router-view />
    </app-layout>
  </v-app>
</template>

<script setup>
import AppLayout from "@/layouts/AppLayout.vue";

import { useTheme } from 'vuetify'

const { global: theme } = useTheme()
</script>

<style scoped></style>