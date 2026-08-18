import { API_ENDPOINTS, apiClient } from "@/lib/api";
import type {
  DocumentListOptions,
  DocumentMetadata,
  PaginatedDocuments,
} from "@/types/api";

function queryString(options: DocumentListOptions) {
  const params = new URLSearchParams({
    page: String(options.page),
    page_size: String(options.page_size),
    sort_by: options.sort_by,
    sort_order: options.sort_order,
  });

  if (options.search.trim()) params.set("search", options.search.trim());
  if (options.file_type) params.set("file_type", options.file_type);
  if (options.status) params.set("status", options.status);

  return params.toString();
}

export const documentService = {
  list(options: DocumentListOptions) {
    return apiClient.get<PaginatedDocuments>(
      `${API_ENDPOINTS.documents}?${queryString(options)}`,
    );
  },

  get(id: string) {
    return apiClient.get<DocumentMetadata>(`${API_ENDPOINTS.documents}/${id}`);
  },

  upload(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.postForm<DocumentMetadata>(API_ENDPOINTS.documents, formData);
  },
};
