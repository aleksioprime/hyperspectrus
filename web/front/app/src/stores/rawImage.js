import { defineStore } from "pinia";
import resources from "@/services/resources";
import logger from "@/common/helpers/logger";


export const useRawImageStore = defineStore("rawImage", {
  state: () => ({}),
  getters: {},
  actions: {
    // Загрузка исходных изображений
    async uploadRawImages(data) {
      const res = await resources.rawImage.uploadRawImages(data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Обновление данных об изображении по его ID
    async updateRawImage(rawImageId, data) {
      const res = await resources.rawImage.partialUpdateRawImage(rawImageId, data);
      if (res.__state === "success") {
        return res.data
      }
      return null
    },
    // Удаление изображения по его ID
    async deleteRawImage(rawImageId) {
      const res = await resources.rawImage.deleteRawImage(rawImageId);
      if (res.__state === "success") {
        return true
      }
      return null
    },
    // Удаление списка изображений
    async deleteManyRawImage(data) {
      const res = await resources.rawImage.deleteManyRawImage(data);
      if (res.__state === "success") {
        return true
      }
      return null
    },
  }
});