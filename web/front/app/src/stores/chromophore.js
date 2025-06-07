import { defineStore } from "pinia";
import resources from "@/services/resources";


export const useChromophoreStore = defineStore("chromophore", {
  state: () => ({
    chromophores: [],
  }),
  getters: {},
  actions: {
  }
});