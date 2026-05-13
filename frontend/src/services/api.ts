const API_BASE = import.meta.env.VITE_API_URL || "/api";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail || response.statusText);
  }

  return response.json();
}

export const api = {
  // Token
  createToken: (identity: string, roomName: string, metadata?: string) =>
    request<{ token: string; room_name: string; identity: string; server_url: string }>(
      "/token",
      {
        method: "POST",
        body: JSON.stringify({ identity, room_name: roomName, metadata }),
      }
    ),

  // Documents
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, body.detail);
    }

    return response.json();
  },

  ingestText: (text: string, docId?: string, isMarkdown?: boolean) =>
    request("/documents/text", {
      method: "POST",
      body: JSON.stringify({
        text,
        doc_id: docId,
        is_markdown: isMarkdown,
      }),
    }),

  deleteDocument: (docId: string) =>
    request(`/documents/${docId}`, { method: "DELETE" }),

  queryDocuments: (query: string, topK = 5) =>
    request("/documents/query", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    }),

  // Health
  health: () => request<Record<string, unknown>>("/health"),
};