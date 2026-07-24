import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api";
import { getBackendHealthStatus } from "@/services/health/health.service";

describe("getBackendHealthStatus", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("maps a healthy backend response into a connected status", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValue({
      data: {
        status: "healthy",
        version: "0.1.0",
      },
      status: 200,
    });

    await expect(getBackendHealthStatus()).resolves.toEqual({
      connected: true,
      statusLabel: "healthy",
      version: "0.1.0",
    });
  });

  it("returns an offline state when the API request fails", async () => {
    vi.spyOn(apiClient, "get").mockRejectedValue(
      new ApiError("Backend unavailable", {
        statusCode: 503,
      }),
    );

    await expect(getBackendHealthStatus()).resolves.toEqual({
      connected: false,
      statusLabel: "offline",
    });
  });
});
