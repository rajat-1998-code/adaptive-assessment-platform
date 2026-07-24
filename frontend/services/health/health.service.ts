import { apiClient, API_ENDPOINTS, ApiError } from "@/lib/api";
import type { HealthApiResponse, HealthStatusView } from "@/types/api";

export async function getBackendHealthStatus(): Promise<HealthStatusView> {
  try {
    const response = await apiClient.get<HealthApiResponse>(API_ENDPOINTS.health);
    const status = response.data.status.toLowerCase();

    return {
      connected: status === "ok" || status === "healthy",
      statusLabel: response.data.status,
      version: response.data.version,
    };
  } catch (error) {
    if (error instanceof ApiError) {
      return {
        connected: false,
        statusLabel: "offline",
      };
    }

    throw error;
  }
}
