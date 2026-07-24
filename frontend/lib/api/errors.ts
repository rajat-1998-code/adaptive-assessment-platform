export class ApiError extends Error {
  readonly statusCode?: number;
  readonly details?: unknown;

  constructor(message: string, options?: { statusCode?: number; details?: unknown }) {
    super(message);
    this.name = "ApiError";
    this.statusCode = options?.statusCode;
    this.details = options?.details;
  }
}
