<template>
  <h1 class="text-h5 mb-4">Организации</h1>

  <v-btn color="primary" class="my-2" @click="openEditDialog()">
    <v-icon start>mdi-plus</v-icon>
    Добавить
  </v-btn>

  <v-list class="my-3" density="compact" style="background: transparent;">
    <template v-for="(org, index) in organizations" :key="org.id">
      <v-list-item class="org-list-item-bg">

        <!-- Данные -->
        <v-list-item-title>
          <b>{{ org.name }}</b>
        </v-list-item-title>
        <v-list-item-subtitle v-if="org.description">
          {{ org.description }}
        </v-list-item-subtitle>

        <!-- Кнопки редактирования или удаления -->
        <template #append>
          <v-btn icon size="small" @click="openEditDialog(org)">
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn icon size="small" @click="openDeleteDialog(org)" class="ms-2">
            <v-icon color="red">mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-list-item>

    </template>
  </v-list>

  <!-- Модальное окно добавления/редактирования организации -->
  <v-dialog v-model="modalDialogEdit.visible" max-width="500px">
    <v-card>
      <v-card-title>
        {{ modalDialogEdit.editing ? 'Редактировать организацию' : 'Новая организация' }}
      </v-card-title>
      <v-card-text>
        <OrganizationForm ref="organizationFormRef" v-model="modalDialogEdit.form" />
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="modalDialogEdit.visible = false">Отмена</v-btn>
        <v-btn color="primary" @click="submitDialog">
          {{ modalDialogEdit.editing ? 'Сохранить' : 'Создать' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Модальное окно удаления организации -->
  <v-dialog v-model="modalDialogDelete.visible" max-width="400px">
    <v-card>
      <v-card-title>Удалить организацию?</v-card-title>
      <v-card-text>
        Вы уверены, что хотите удалить организацию <strong>
          {{ modalDialogDelete.organization?.name }}</strong>?
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn @click="modalDialogDelete.visible = false">Отмена</v-btn>
        <v-btn color="red" @click="confirmDeleteOrganization">Удалить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

</template>

<script setup>
import { ref, onMounted } from "vue";

import OrganizationForm from "@/components/organizations/OrganizationForm.vue";

import { useOrganizationStore } from "@/stores/organization";
const organizationStore = useOrganizationStore();

const organizations = ref([])

onMounted(async () => {
  organizations.value = await organizationStore.loadOrganizations();
});

// --- ДОБАВЛЕНИЕ/РЕДАКТИРОВАНИЕ ОРГАНИЗАЦИИ ---

// Объект модального окна
const modalDialogEdit = ref({
  visible: false,
  editing: false,
  form: {},
});

// Открытие модального окна для создания организации
const openEditDialog = (organization = null) => {
  modalDialogEdit.value = {
    visible: true,
    editing: !!organization,
    form: organization
      ? { ...organization }
      : { id: null, name: "", description: "" }
  };
};

// Подготовка данных формы для запроса создания/редактирования организациии
const getFormPayload = (form) => ({ ...form });

// Подтверждение создания/редактирования организации
const organizationFormRef = ref();

const submitDialog = async () => {
  const valid = await organizationFormRef.value?.submit();
  if (!valid) return;

  const { form, editing } = modalDialogEdit.value;

  if (editing) {
    await organizationStore.updateOrganization(form.id, getFormPayload(form));
    const index = organizations.value.findIndex(p => p.id === form.id);
    if (index !== -1) organizations.value[index] = { ...organizations.value[index], ...form };
  } else {
    const newOrganization = await organizationStore.createOrganization(getFormPayload(form));
    if (newOrganization) organizations.value.unshift(newOrganization);
  }

  modalDialogEdit.value.visible = false;
};

// --- УДАЛЕНИЕ ОРГАНИЗАЦИИ ---

// Объект модального окна
const modalDialogDelete = ref({
  visible: false,
  organization: null,
});

// Вызов модального окна удаления
const openDeleteDialog = (organization) => {
  modalDialogDelete.value = { visible: true, organization };
};

// Подтверждение удаления в модальном окне

const confirmDeleteOrganization = async () => {
  const organization = modalDialogDelete.value.organization;

  const success = await organizationStore.deleteOrganization(organization.id);
  if (success) organizations.value = organizations.value.filter((p) => p.id !== organization.id);

  modalDialogDelete.value.visible = false;
};
</script>

<style scoped>
.org-list-item-bg {
  background: #f5f7fa;
  border-radius: 14px;
  margin-bottom: 8px;
  transition: background 0.2s;
  padding: 10px 0 10px 0;
}

.org-list-item-bg:hover {
  background: #e3eaf5;
}
</style>