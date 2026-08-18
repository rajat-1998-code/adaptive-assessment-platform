export interface ApiErrorResponse {
  error: string;
  path?: string;
  details?: unknown;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_email_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AuthStatusResponse {
  enabled: boolean;
  token_type: string;
  access_token_expire_minutes: number;
  refresh_token_expire_days: number;
}

export interface AuthMessageResponse {
  message: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface MagicLinkRequest {
  email: string;
}

export interface VerifyEmailRequest {
  code: string;
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

export interface DocumentMetadata {
  id: string;
  title: string;
  original_filename: string;
  content_type: string | null;
  file_size: number | null;
  processing_status: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedDocuments {
  items: DocumentMetadata[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export type DocumentSortBy =
  | "created_at"
  | "title"
  | "original_filename"
  | "processing_status";

export interface DocumentListOptions {
  page: number;
  page_size: number;
  search: string;
  file_type: string;
  status: string;
  sort_by: DocumentSortBy;
  sort_order: "asc" | "desc";
}
