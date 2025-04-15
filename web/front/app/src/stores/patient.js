import { defineStore } from "pinia";
import resources from "@/services/resources";


export const usePatientStore = defineStore("patient", {
  state: () => ({
    patients: [],
  }),
  getters: {

  },
  actions: {
    // Загрузка списка пациентов (пагинированный)
    async loadPatients(config) {
      const res = await resources.patient.getPatients(config);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Загрузка детальной информации о пациенте по ID
    async loadPatientDetailed(id) {
      const res = await resources.patient.getPatientDetailed(id);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление пациента
    async createPatient(data) {
      const res = await resources.patient.createPatient(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Обновление пациента
    async updatePatient(id, data) {
      const res = await resources.patient.partialUpdatePatient(id, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление пациента
    async deletePatient(id) {
      const res = await resources.patient.deletePatient(id);
      if (res.__state === "success") {
        return true
      }
      return null
    },
  }
});