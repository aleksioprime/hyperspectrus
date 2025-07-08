import { ApiService } from "@/services/api/api.service";

export class OrganizationResource extends ApiService {
  constructor() {
    super();
  }

  getOrganizations(params) {
    return this.$get(`/api/v1/organizations/`, params);
  }

  createOrganization(data) {
    return this.$post(`/api/v1/organizations/`, data);
  }

  updateOrganization(id, data) {
    return this.$patch(`/api/v1/organizations/${id}/`, data);
  }

  deleteOrganization(id) {
    return this.$delete(`/api/v1/organizations/${id}/`);
  }

}