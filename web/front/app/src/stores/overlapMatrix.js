import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useOverlapMatrixStore = defineStore("overlapMatrix", {
  state: () => ({
    overlapMatrixes: [],
  }),
  getters: {},
  actions: {
  }
});