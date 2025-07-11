<template>
  <div>
    <h1 class="text-h5 mb-4">Справочник хромофоров</h1>

    <v-btn color="primary" class="mb-4" @click="openEditDialog()">
      <v-icon start>mdi-plus</v-icon>
      Добавить хромофор
    </v-btn>

    <!-- Таблица хромофоров -->
    <v-table>
      <thead>
        <tr>
          <th style="width: 150px">Название</th>
          <th style="width: 120px;">Обозначение</th>
          <th>Описание</th>
          <th style="width: 130px;"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="chrom in chromophores" :key="chrom.id">
          <td>{{ chrom.name }}</td>
          <td>{{ chrom.symbol }}</td>
          <td>{{ chrom.description }}</td>
          <td class="text-center">
            <v-btn icon class="ma-1" size="small" @click="openEditDialog(chrom)">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon class="ma-1" size="small" color="red" @click="openDeleteDialog(chrom)">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>


    <!-- Модальное окно добавления/редактирования хромофора -->
    <v-dialog v-model="modalDialogEdit.visible" max-width="500px">
      <v-card>
        <v-card-title>
          {{ modalDialogEdit.editing ? 'Редактировать хромофор' : 'Новый хромофор' }}
        </v-card-title>
        <v-card-text>
          <ChromophoreForm ref="chromophoreFormRef" v-model="modalDialogEdit.form" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="modalDialogEdit.visible = false">Отмена</v-btn>
          <v-btn color="primary" @click="submitDialog">
            {{ modalDialogEdit.editing ? 'Сохранить' : 'Создать' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Модальное окно удаления хромофора -->
    <v-dialog v-model="modalDialogDelete.visible" max-width="400px">
      <v-card>
        <v-card-title>Удалить хромофор?</v-card-title>
        <v-card-text>
          Вы уверены, что хотите удалить хромофор <strong>
            {{ modalDialogDelete.chromophore?.name }}</strong>?
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="modalDialogDelete.visible = false">Отмена</v-btn>
          <v-btn color="red" @click="confirmDeleteChromophore">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

import ChromophoreForm from "@/components/chromophores/ChromophoreForm.vue";

import { useChromophoreStore } from "@/stores/chromophore";
const chromophoreStore = useChromophoreStore();

const chromophores = ref([]);

// --- ДОБАВЛЕНИЕ/РЕДАКТИРОВАНИЕ ХРОМОФОРОВ ---

// Объект модального окна
const modalDialogEdit = ref({
  visible: false,
  editing: false,
  form: {},
});

const openEditDialog = (chromophore = null) => {
  modalDialogEdit.value = {
    visible: true,
    editing: !!chromophore,
    form: chromophore
      ? { ...chromophore }
      : { id: null, name: "", symbol: "", description: "" }
  };
};

// Подготовка данных формы для запроса создания/редактирования хромофора
const getFormPayload = (form) => ({ ...form });

// Подтверждение создания/редактирования хромофора
const chromophoreFormRef = ref();

const submitDialog = async () => {
  const valid = await chromophoreFormRef.value?.submit();
  if (!valid) return;

  const { form, editing } = modalDialogEdit.value;

  if (editing) {
    await chromophoreStore.updateChromophore(form.id, getFormPayload(form));
    const index = chromophores.value.findIndex(p => p.id === form.id);
    if (index !== -1) chromophores.value[index] = { ...chromophores.value[index], ...form };
  } else {
    const newChromophore = await chromophoreStore.createChromophore(getFormPayload(form));
    if (newChromophore) {
      chromophores.value.push(newChromophore);
      chromophores.value.sort((a, b) => a.name.localeCompare(b.name));
    }
  }

  modalDialogEdit.value.visible = false;
};

// --- УДАЛЕНИЕ ХРОМОФОРА ---

// Объект модального окна
const modalDialogDelete = ref({
  visible: false,
  chromophore: null,
});

// Вызов модального окна удаления
const openDeleteDialog = (chromophore) => {
  modalDialogDelete.value = { visible: true, chromophore };
};

// Подтверждение удаления в модальном окне

const confirmDeleteChromophore = async () => {
  const chromophore = modalDialogDelete.value.chromophore;

  const success = await chromophoreStore.deleteChromophore(chromophore.id);
  if (success) chromophores.value = chromophores.value.filter((p) => p.id !== chromophore.id);

  modalDialogDelete.value.visible = false;
};

onMounted(async () => {
  chromophores.value = await chromophoreStore.loadChromophores();
});
</script>