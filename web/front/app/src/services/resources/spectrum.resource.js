import { ApiService } from "@/services/api/api.service";

export class SpectrumResource extends ApiService {
  constructor() {
    super();
  }

  getSpectra(deviceId, config) {
    return this.$get(`/api/v1/devices/${deviceId}/spectra/`, config);
  }

  createSpectrum(deviceId, data) {
    return this.$post(`/api/v1/devices/${deviceId}/spectra/`, data);
  }

  updateSpectrum(deviceId, spectrumId, data) {
    return this.$patch(`/api/v1/devices/${deviceId}/spectra/${spectrumId}/`, data);
  }

  deleteSpectrum(deviceId, spectrumId) {
    return this.$delete(`/api/v1/devices/${deviceId}/spectra/${spectrumId}/`);
  }
}