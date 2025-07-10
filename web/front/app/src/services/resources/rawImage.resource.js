import { ApiService } from "@/services/api/api.service";

export class RawImageResource extends ApiService {
  constructor() {
    super();
  }

  uploadRawImages(data) {
    return this.$post(`/api/v1/raw_images/upload/`, data);
  }

  partialUpdateRawImage(id, data) {
    return this.$patch(`/api/v1/raw_images/${id}/`, data);
  }

  deleteRawImage(id) {
    return this.$delete(`/api/v1/raw_images/${id}/`);
  }

  deleteManyRawImage(data) {
    return this.$post(`/api/v1/raw_images/delete/`, data);
  }
}