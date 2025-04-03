import { ApiService } from "@/services/api/api.service";

export class GenerateResource extends ApiService {
  constructor() {
    super();
  }

  async generateReportProvider(provider, data) {
    return this.$post(`/api/v1/generate/${provider}`, data);
  }
}