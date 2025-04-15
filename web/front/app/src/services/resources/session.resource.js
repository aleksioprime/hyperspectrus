import { ApiService } from "@/services/api/api.service";

export class SessionResource extends ApiService {
  constructor() {
    super();
  }

  getSessionDetailed(patientId, sessionId) {
    return this.$get(`/api/v1/patients/${patientId}/sessions/${sessionId}`);
  }

  createSession(patientId, data) {
    return this.$post(`/api/v1/patients/${patientId}/sessions/`, data);
  }

  partialUpdatePatient(patientId, sessionId, data) {
    return this.$patch(`/api/v1/patients/${patientId}/sessions/${sessionId}`, data);
  }

  deletePatient(patientId, sessionId, data) {
    return this.$delete(`/api/v1/patients/${patientId}/sessions/${sessionId}`, data);
  }
}