export interface ApiErrorResponse {
  error: string;
  path?: string;
  details?: unknown;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
}

export interface HealthApiResponse {
  status: string;
  version?: string;
}

export interface HealthStatusView {
  connected: boolean;
  statusLabel: string;
  version?: string;
}
