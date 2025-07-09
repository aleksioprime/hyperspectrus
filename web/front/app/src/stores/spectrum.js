import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useSpectrumStore = defineStore("spectrum", {
  state: () => ({
    spectra: [],
  }),
  getters: {},
  actions: {
    // Загрузка списка спектров
    async loadSpectra(deviceId, config) {
      const res = await resources.spectrum.getSpectra(deviceId, config);
      if (res.__state === "success") {
        this.spectra = res.data
        return res.data
      }
      return null
    },
    // Добавление спектра
    async createSpectrum(deviceId, data) {
      const res = await resources.spectrum.createSpectrum(deviceId, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Обновление спектра
    async updateSpectrum(deviceId, spectrumId, data) {
      const res = await resources.spectrum.updateSpectrum(deviceId, spectrumId, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление спектра
    async deleteSpectrum(deviceId, spectrumId) {
      const res = await resources.spectrum.deleteSpectrum(deviceId, spectrumId);
      if (res.__state === "success") {
        return true
      }
      return null
    },
  }
});