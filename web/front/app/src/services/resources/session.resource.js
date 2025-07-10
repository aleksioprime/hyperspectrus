import { ApiService } from "@/services/api/api.service";

export class SessionResource extends ApiService {
  constructor() {
    super();
  }

  getSessionDetailed(patientId, sessionId) {
    return this.$get(`/api/v1/patients/${patientId}/sessions/${sessionId}/`);
  }

  createSession(patientId, data) {
    return this.$post(`/api/v1/patients/${patientId}/sessions/`, data);
  }

  partialUpdateSession(patientId, sessionId, data) {
    return this.$patch(`/api/v1/patients/${patientId}/sessions/${sessionId}/`, data);
  }

  deleteSession(patientId, sessionId) {
    return this.$delete(`/api/v1/patients/${patientId}/sessions/${sessionId}/`);
  }

  processSession(patientId, sessionId) {
    return this.$post(`/api/v1/patients/${patientId}/sessions/${sessionId}/process/`);
  }

  processSessionStatus(patientId, sessionId) {
    return this.$get(`/api/v1/patients/${patientId}/sessions/${sessionId}/process/status/`);
  }
}