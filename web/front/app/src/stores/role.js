import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useRoleStore = defineStore("role", {
  state: () => ({}),
  getters: {

  },
  actions: {
    // Загрузка списка пользователей (пагинированный)
    async loadRoles(config) {
      const res = await resources.role.getRoles(config);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
  },
})