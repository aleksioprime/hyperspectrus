import { ApiService } from "@/services/api/api.service";

export class UserResource extends ApiService {
  constructor() {
    super();
  }

  getUserInfo() {
    return this.$get(`api/v1/user/me`, params);
  }
}