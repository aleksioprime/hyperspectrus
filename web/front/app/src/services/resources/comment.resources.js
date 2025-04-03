import { ApiService } from "@/services/api/api.service";

export class CommentResource extends ApiService {
  constructor() {
    super();
  }

  getRequestComments(request_id, config) {
    return this.$get(`/api/v1/requests/${request_id}/comments`, config);
  }

  createComment(request_id, data) {
    return this.$post(`/api/v1/requests/${request_id}/comments`, data);
  }

  partialUpdateComment(request_id, comment_id, data) {
    return this.$patch(`/api/v1/requests/${request_id}/comments/${comment_id}`, data);
  }

  deleteComment(request_id, comment_id) {
    return this.$delete(`/api/v1/requests/${request_id}/comments/${comment_id}`);
  }
}