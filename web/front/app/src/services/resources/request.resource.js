import { ApiService } from "@/services/api/api.service";

export class RequestResource extends ApiService {
  constructor() {
    super();
  }

  loadMyRequests() {
    return this.$get(`/api/v1/requests/me`);
  }

  loadGlobalRequests() {
    return this.$get(`/api/v1/requests/global`);
  }

  getRequestDetailed(id) {
    return this.$get(`/api/v1/requests/${id}`);
  }

  createRequest(data) {
    return this.$post(`/api/v1/requests`, data);
  }

  partialUpdateRequest(id, data) {
    return this.$patch(`/api/v1/requests/${id}`, data);
  }

  deleteRequest(id, data) {
    return this.$delete(`/api/v1/requests/${id}`, data);
  }
}