import { AxiosError } from "axios";

export class ApiError extends Error {
  constructor(message, response) {
    super(message);
    this.response = response;
  }
}

export function getApiError(e) {
  if (e instanceof AxiosError) {
    return new ApiError(
      e.response?.data?.error?.message ?? e.message,
      e.response
    );
  } else {
    return new ApiError(e.message, e.response);
  }
}
