import { ApiService } from "@/services/api/api.service";

export class DeviceResource extends ApiService {
  constructor() {
    super();
  }

  getDevices(config) {
    return this.$get(`/api/v1/devices/`, config);
  }

  getDeviceDetailed(id) {
    return this.$get(`/api/v1/devices/${id}/`);
  }

  createDevice(id, data) {
    return this.$post(`/api/v1/devices/${id}/`, data);
  }

  partialUpdatePatient(id, data) {
    return this.$patch(`/api/v1/devices/${id}/`, data);
  }

  deletePatient(id, data) {
    return this.$delete(`/api/v1/devices/${id}/`, data);
  }
}