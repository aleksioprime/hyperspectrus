import { ApiService } from "@/services/api/api.service";

export class ChromophoreResource extends ApiService {
  constructor() {
    super();
  }

  getChromophores(config) {
    return this.$get(`/api/v1/chromophores/`, config);
  }

  createChromophore(data) {
    return this.$post(`/api/v1/chromophores/`, data);
  }

  updateChromophore(id, data) {
    return this.$patch(`/api/v1/chromophores/${id}/`, data);
  }

  deleteChromophore(id) {
    return this.$delete(`/api/v1/chromophores/${id}/`);
  }

}