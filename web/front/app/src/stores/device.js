import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useDeviceStore = defineStore("device", {
  state: () => ({
    devices: [],
  }),
  getters: {

  },
  actions: {
    // Загрузка списка пациентов (пагинированный)
    async loadDevices(config) {
      const res = await resources.device.getDevices(config);
      if (res.__state === "success") {
        this.devices = res.data
        return res.data
      }
      return null
    },
    // Загрузка детальной информации о пациенте по ID
    async loadDeviceDetailed(id) {
      const res = await resources.device.getDeviceDetailed(id);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление пациента
    async createDevice(data) {
      const res = await resources.device.createDevice(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Обновление пациента
    async updateDevice(id, data) {
      const res = await resources.device.partialUpdateDevice(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление пациента
    async deleteDevice(id) {
      const res = await resources.device.deleteDevice(id);
      if (res.__state === "success") {
        return true
      }
      return null
    },
  }
});