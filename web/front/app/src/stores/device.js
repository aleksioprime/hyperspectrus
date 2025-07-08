import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useDeviceStore = defineStore("device", {
  state: () => ({}),
  getters: {

  },
  actions: {
    // Загрузка списка устройств
    async loadDevices(config) {
      const res = await resources.device.getDevices(config);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Загрузка детальной информации об устройстве
    async loadDeviceDetailed(id) {
      const res = await resources.device.getDeviceDetailed(id);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление устройства
    async createDevice(data) {
      const res = await resources.device.createDevice(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Обновление устройства
    async updateDevice(id, data) {
      const res = await resources.device.updateDevice(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление устройства
    async deleteDevice(id) {
      const res = await resources.device.deleteDevice(id);
      if (res.__state === "success") {
        return true
      }
      return null
    },
    // Заполнение матрицы коэффициентов рандомными числами
    async randomFillOverlapsDevice(id) {
      const res = await resources.device.randomFillOverlapsDevice(id);
      if (res.__state === "success") {
        return true
      }
      return null
    }
  }
});