import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useUserStore = defineStore("user", {
  state: () => ({}),
  getters: {

  },
  actions: {
    // Загрузка списка пользователей (пагинированный)
    async loadUsers(config) {
      const res = await resources.user.getUsers(config);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление пользователя
    async createUser(data) {
      const res = await resources.user.createUser(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Редактирование пользователя
    async updateUser(id, data) {
      const res = await resources.user.updateUser(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление пользователя
    async deleteUser(id) {
      const res = await resources.user.deleteUser(id);
      if (res.__state === "success") {
        return true
      }
      return null
    },
    // Сброс пароля пользователя
    async resetPassword(id, data) {
      const res = await resources.user.resetPassword(id, data);
      if (res.__state === "success") {
        return true
      }
      return null
    },
    // Обновление изображения пользователя
    async uploadPhoto(id, data) {
      const res = await resources.user.uploadPhoto(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление изображения пользователя
    async deletePhoto(id) {
      const res = await resources.user.deletePhoto(id);
      if (res.__state === "success") {
        return res.data
      }
      return null
    }
  },
})