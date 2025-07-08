import { ApiService } from "@/services/api/api.service";

export class RoleResource extends ApiService {
  constructor() {
    super();
  }

  getRoles(params) {
    return this.$get(`/api/v1/roles/`, params);
  }

}