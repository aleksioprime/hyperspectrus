import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useChromophoreStore = defineStore("chromophore", {
  state: () => ({}),
  getters: {},
  actions: {
    // Загрузка списка хромофоров
    async loadChromophores(config) {
      const res = await resources.chromophore.getChromophores(config);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление хромофора
    async createChromophore(data) {
      const res = await resources.chromophore.createChromophore(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Редактирование хромофора
    async updateChromophore(id, data) {
      const res = await resources.chromophore.updateChromophore(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление хромофора
    async deleteChromophore(id) {
      const res = await resources.chromophore.deleteChromophore(id);
      if (res.__state === "success") {
        return true
      }
      return null
    },
  }
});