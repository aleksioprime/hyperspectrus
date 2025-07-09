import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useSessionStore = defineStore("session", {
  state: () => ({
    sessions: [],
  }),
  getters: {

  },
  actions: {
    // Загрузка детальной информации о сеансах пациента по их ID
    async loadSessionDetailed(patientId, sessionId) {
      const res = await resources.session.getSessionDetailed(patientId, sessionId);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Добавление сеанса к пациенту по его ID
    async createSession(patientId, data) {
      const res = await resources.session.createSession(patientId, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Обновление сеанса у пациента по их ID
    async updateSession(patientId, sessionId, data) {
      const res = await resources.session.partialUpdateSession(patientId, sessionId, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление сеанса у пациента по их ID
    async deleteSession(patientId, sessionId) {
      const res = await resources.session.deleteSession(patientId, sessionId);
      if (res.__state === "success") {
        return true
      }
      return null
    },
    // Запуск обработки данных сеанса у пациента по их ID
    async processSession(patientId, sessionId) {
      const res = await resources.session.processSession(patientId, sessionId);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Получение статуса обработки данных сеанса у пациента по их ID
    async processSessionStatus(patientId, sessionId) {
      const res = await resources.session.processSessionStatus(patientId, sessionId);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
  }
});