import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useOverlapMatrixStore = defineStore("overlapMatrix", {
  state: () => ({}),
  getters: {},
  actions: {
    // Загрузка списка коэффициентов
    async loadOverlapCoefficients(config) {
      const res = await resources.overlapMatrix.getOverlapCoefficients(config);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление устройства
    async createOverlapCoefficient(data) {
      const res = await resources.overlapMatrix.createOverlapCoefficient(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Обновление устройства
    async updateOverlapCoefficient(id, data) {
      const res = await resources.overlapMatrix.updateOverlapCoefficient(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление устройства
    async deleteOverlapCoefficient(id) {
      const res = await resources.overlapMatrix.deleteOverlapCoefficient(id);
      if (res.__state === "success") {
        return true
      }
      return null
    },
  }
});