import { env } from "@/config/env";
import type { ApiErrorResponse, ApiResponse } from "@/types/api";

import { ApiError } from "./errors";

function buildUrl(path: string) {
  const baseUrl = env.serverApiBaseUrl || env.apiBaseUrl;

  if (!baseUrl) {
    throw new ApiError(
      "API_BASE_URL or NEXT_PUBLIC_API_BASE_URL is not configured. Set one before calling the backend.",
    );
  }

  return new URL(path, baseUrl).toString();
}

export async function httpRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiResponse<T>> {
  const response = await fetch(buildUrl(path), {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  let payload: T | ApiErrorResponse | null = null;

  try {
    payload = (await response.json()) as T | ApiErrorResponse;
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const errorPayload = payload as ApiErrorResponse | null;
    throw new ApiError(errorPayload?.error ?? "API request failed", {
      statusCode: response.status,
      details: errorPayload?.details,
    });
  }

  return {
    data: payload as T,
    status: response.status,
  };
}
