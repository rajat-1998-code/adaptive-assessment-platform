export const env = {
  serverApiBaseUrl: process.env.API_BASE_URL?.replace(/\/+$/, "") ?? "",
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "",
} as const;
