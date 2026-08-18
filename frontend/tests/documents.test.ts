import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/lib/api";
import { documentService } from "@/services/documents/document.service";

describe("documentService", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("builds library query parameters", async () => {
    const get = vi.spyOn(apiClient, "get").mockResolvedValue({
      data: { items: [], page: 1, page_size: 20, total: 0, pages: 0 },
      status: 200,
    });

    await documentService.list({
      page: 2,
      page_size: 20,
      search: "guide notes",
      file_type: "pdf",
      status: "uploaded",
      sort_by: "title",
      sort_order: "asc",
    });

    expect(get).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/v1/documents?page=2&page_size=20&sort_by=title&sort_order=asc&search=guide+notes&file_type=pdf&status=uploaded",
      ),
    );
  });

  it("submits a file as multipart form data", async () => {
    const postForm = vi.spyOn(apiClient, "postForm").mockResolvedValue({
      data: {} as never,
      status: 201,
    });
    const file = new File(["hello"], "notes.txt", { type: "text/plain" });

    await documentService.upload(file);

    const [path, formData] = postForm.mock.calls[0];
    expect(path).toBe("/api/v1/documents");
    expect(formData).toBeInstanceOf(FormData);
    expect((formData as FormData).get("file")).toBe(file);
  });
});
