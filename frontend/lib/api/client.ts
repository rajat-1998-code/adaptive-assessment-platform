import type { ApiResponse } from "@/types/api";

import { httpRequest } from "./http";

class ApiClient {
  get<T>(path: string, init?: Omit<RequestInit, "method">): Promise<ApiResponse<T>> {
    return httpRequest<T>(path, {
      ...init,
      method: "GET",
    });
  }
}

export const apiClient = new ApiClient();
