import { ApiService } from "@/services/api/api.service";

export class PatientResource extends ApiService {
  constructor() {
    super();
  }

  getPatients(config) {
    return this.$get(`/api/v1/patients/`, config);
  }

  getPatientDetailed(id) {
    return this.$get(`/api/v1/patients/${id}/`);
  }

  createPatient(data) {
    return this.$post(`/api/v1/patients/`, data);
  }

  partialUpdatePatient(id, data) {
    return this.$patch(`/api/v1/patients/${id}/`, data);
  }

  deletePatient(id) {
    return this.$delete(`/api/v1/patients/${id}/`);
  }
}