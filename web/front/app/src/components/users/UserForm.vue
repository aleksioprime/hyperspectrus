<template>
  <v-form ref="formRef" @submit.prevent="onSubmit">
    <v-text-field v-model="form.username" label="Логин" :rules="usernameRules" required clearable />
    <div v-if="isCreate">
      <v-row class="py-2">
        <v-col cols="12" md="6" class="py-0">
          <v-text-field v-model="form.password" label="Пароль" :type="'password'" :rules="passwordRules" required
            clearable />
        </v-col>
        <v-col cols="12" md="6" class="py-0">
          <v-text-field v-model="form.repeat_password" label="Повторите пароль" :type="'password'"
            :rules="repeatPasswordRules(form.password)" required clearable />
        </v-col>
      </v-row>
    </div>
    <v-text-field v-model="form.email" label="E-Mail" :rules="emailRules" required clearable />
    <v-row class="py-2">
      <v-col cols="12" md="6" class="py-0">
        <v-text-field v-model="form.first_name" label="Имя" :rules="nameRules" required clearable />
      </v-col>
      <v-col cols="12" md="6" class="py-0">
        <v-text-field v-model="form.last_name" label="Фамилия" :rules="nameRules" required clearable />
      </v-col>
    </v-row>
    <v-select v-model="form.organization" :items="organizations" item-title="name" item-value="id" label="Организация"
      :rules="[rules.required]" clearable required />
    <v-select v-model="form.roles" :items="roles" item-title="display_name" item-value="id" label="Роли" multiple chips
      :rules="[rules.requiredList]" clearable required />
    <v-checkbox v-if="canEditIsAdmin" v-model="form.is_superuser" label="Суперпользователь" :true-value="true"
      :false-value="false" />
  </v-form>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import rules from "@/common/helpers/rules";

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();

import { useRoleStore } from "@/stores/role";
const roleStore = useRoleStore();
const roles = ref([]);

import { useOrganizationStore } from "@/stores/organization";
const organizationStore = useOrganizationStore();
const organizations = ref([]);

// Текущий пользователь - суперпользователь?
const canEditIsAdmin = computed(() => authStore.user?.is_superuser);

const props = defineProps({
  modelValue: { type: Object, required: false, default: () => ({}) },
  isCreate: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

// Локальное состояние формы
const form = reactive({
  first_name: "",
  last_name: "",
  email: "",
  username: "",
  password: "",
  repeat_password: "",
  is_admin: "",
  roles: [],
  organization: null,
  is_superuser: false,
});

// Валидация полей
const nameRules = [rules.required, rules.minLength(2), rules.maxLength(30), rules.onlyLetters];
const emailRules = [rules.required, rules.email];
const usernameRules = [rules.required, rules.username, rules.minLength(3), rules.maxLength(20)];
const passwordRules = [rules.required, rules.minLength(6)];
const repeatPasswordRules = (password) => [rules.required, rules.sameAs(password, "Пароли не совпадают")];

// Синхронизация изменения внешнего modelValue с внутренним
watch(
  () => props.modelValue?.id,
  (newId, oldId) => {
    if (newId !== oldId) {
      Object.assign(form, { ...props.modelValue });
      form.roles = (props.modelValue?.roles || []).map(r => typeof r === "object" ? r.id : r);
    }
  },
  { immediate: true }
);

// Синхронизация изменения внутренего modelValue с внешним
watch(
  () => ({ ...form, roles: [...form.roles] }),
  (val) => emit("update:modelValue", val)
);

// Отправка формы
const formRef = ref();

const onSubmit = async () => {
  const { valid } = await formRef.value?.validate();
  return valid
};

defineExpose({ submit: onSubmit });

const setDefaultRoles = () => {
  const defaultRole = roles.value.find(r => r.name === "employee") || roles.value.find(r => r.name === "user");
  if (defaultRole) form.roles = [defaultRole.id];
}

onMounted(async () => {
  roles.value = await roleStore.loadRoles();
  organizations.value = await organizationStore.loadOrganizations();

  // Если создаём нового пользователя — выбрать роль по умолчанию
  if (props.isCreate) setDefaultRoles();
});
</script>