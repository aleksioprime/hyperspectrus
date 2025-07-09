import { ApiService } from "@/services/api/api.service";

export class OverlapMatrixResource extends ApiService {
  constructor() {
    super();
  }

  getOverlapCoefficients(config) {
    return this.$get(`/api/v1/overlaps/`, config);
  }

  createOverlapCoefficient(data) {
    return this.$post(`/api/v1/overlaps/`, data);
  }

  updateOverlapCoefficient(id, data) {
    return this.$patch(`/api/v1/overlaps/${id}/`, data);
  }

  deleteOverlapCoefficient(id, data) {
    return this.$delete(`/api/v1/overlaps/${id}/`, data);
  }
}