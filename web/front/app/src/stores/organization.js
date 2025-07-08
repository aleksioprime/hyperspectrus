import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useOrganizationStore = defineStore("organization", {
  state: () => ({}),
  getters: {

  },
  actions: {
    // Загрузка списка организаций
    async loadOrganizations(config) {
      const res = await resources.organization.getOrganizations(config);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление организации
    async createOrganization(data) {
      const res = await resources.organization.createOrganization(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Редактирование организации
    async updateOrganization(id, data) {
      const res = await resources.organization.updateOrganization(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление организации
    async deleteOrganization(id) {
      const res = await resources.organization.deleteOrganization(id);
      if (res.__state === "success") {
        return true
      }
      return null
    },
  }
})