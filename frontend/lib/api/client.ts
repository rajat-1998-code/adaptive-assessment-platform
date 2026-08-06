import type { ApiResponse } from "@/types/api";

import { httpRequest } from "./http";

class ApiClient {
  get<T>(path: string, init?: Omit<RequestInit, "method">): Promise<ApiResponse<T>> {
    return httpRequest<T>(path, {
      ...init,
      method: "GET",
    });
  }

  post<T>(
    path: string,
    body?: unknown,
    init?: Omit<RequestInit, "body" | "method">,
  ): Promise<ApiResponse<T>> {
    return httpRequest<T>(path, {
      ...init,
      body: body === undefined ? undefined : JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
      method: "POST",
    });
  }
}

export const apiClient = new ApiClient();
