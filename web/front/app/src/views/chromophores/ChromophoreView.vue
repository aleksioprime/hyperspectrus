<template>
  <div>
    <h1 class="text-h5 mb-4">Параметры хромофоров</h1>

    <v-snackbar v-model="snackbar.show" :timeout="4000" color="red" variant="tonal">
      {{ snackbar.text }}
    </v-snackbar>

    <v-btn color="primary" class="mb-4" @click="openCreateDialog">
      <v-icon start>mdi-plus</v-icon>
      Добавить хромофор
    </v-btn>

    <v-table>
      <thead>
        <tr>
          <th>Название</th>
          <th>Краткое имя</th>
          <th>Описание</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="chrom in chromophores" :key="chrom.id">
          <td>{{ chrom.name }}</td>
          <td>{{ chrom.short_name }}</td>
          <td>{{ chrom.description }}</td>
          <td>
            <v-btn icon size="small" @click="openEditDialog(chrom)">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon size="small" color="red" @click="confirmDeleteChromophore(chrom)">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>

    <!-- Диалог создания/редактирования -->
    <v-dialog v-model="dialog.visible" max-width="400px">
      <v-card>
        <v-card-title>
          {{ dialog.editing ? "Редактировать хромофор" : "Добавить хромофор" }}
        </v-card-title>
        <v-card-text>
          <v-text-field v-model="dialog.form.name" label="Название" required />
          <v-text-field v-model="dialog.form.short_name" label="Краткое имя" />
          <v-text-field v-model="dialog.form.description" label="Описание" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="dialog.visible = false">Отмена</v-btn>
          <v-btn color="primary" @click="submitDialog">
            {{ dialog.editing ? "Сохранить" : "Создать" }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог удаления -->
    <v-dialog v-model="deleteDialog.visible" max-width="400px">
      <v-card>
        <v-card-title>Удалить хромофор?</v-card-title>
        <v-card-text>
          Вы уверены, что хотите удалить хромофор <strong>{{ deleteDialog.chrom?.name }}</strong>?
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn @click="deleteDialog.visible = false">Отмена</v-btn>
          <v-btn color="red" @click="deleteChromophore">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useChromophoreStore } from "@/stores/chromophore"; // реализуй store или подставь API
const chromophoreStore = useChromophoreStore();

const chromophores = ref([]);
const snackbar = ref({ show: false, text: "" });

const dialog = ref({
  visible: false,
  editing: false,
  form: { id: null, name: "", short_name: "", description: "" },
});

const deleteDialog = ref({ visible: false, chrom: null });

// CRUD методы

const loadChromophores = async () => {
  chromophores.value = await chromophoreStore.loadChromophores();
};

const openCreateDialog = () => {
  dialog.value = {
    visible: true,
    editing: false,
    form: { id: null, name: "", short_name: "", description: "" },
  };
};

const openEditDialog = (chrom) => {
  dialog.value = {
    visible: true,
    editing: true,
    form: { ...chrom },
  };
};

const submitDialog = async () => {
  const { form, editing } = dialog.value;
  if (!form.name) {
    snackbar.value = { show: true, text: "Заполните название" };
    return;
  }

  if (editing) {
    await chromophoreStore.updateChromophore(form.id, form);
    const idx = chromophores.value.findIndex((c) => c.id === form.id);
    if (idx !== -1) chromophores.value[idx] = { ...form };
  } else {
    const newChrom = await chromophoreStore.createChromophore(form);
    if (newChrom) chromophores.value.unshift(newChrom);
  }
  dialog.value.visible = false;
};

const confirmDeleteChromophore = (chrom) => {
  deleteDialog.value = { visible: true, chrom };
};

const deleteChromophore = async () => {
  const chrom = deleteDialog.value.chrom;
  await chromophoreStore.deleteChromophore(chrom.id);
  chromophores.value = chromophores.value.filter((c) => c.id !== chrom.id);
  deleteDialog.value.visible = false;
};

onMounted(loadChromophores);
</script>