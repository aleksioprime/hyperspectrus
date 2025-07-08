import { ApiService } from "@/services/api/api.service";

export class AuthService extends ApiService {
  constructor() {
    super();
  }

  whoAmI() {
    return this.$get(`/api/v1/users/me/`);
  }

  login(data) {
    return this.$post(`/api/v1/login/`, data);
  }

  refresh(params) {
    return this.$post(`/api/v1/refresh/`, params);
  }

  logout(params) {
    return this.$post(`/api/v1/logout/`, params);
  }
}
