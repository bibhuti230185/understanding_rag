const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
export const DEV_TOKEN = import.meta.env.VITE_DEV_BEARER_TOKEN ?? "local-dev-token";

export type Citation = {
  document_id: string;
  version_id: string;
  chunk_id: string;
  page_number?: number | null;
  excerpt?: string | null;
};

export type DocumentRecord = {
  document_id: string;
  file_name: string;
  media_type: string;
  status: "queued" | "processing" | "indexed" | "failed" | "deleted";
  current_version_id: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  message_id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  status?: "completed" | "insufficient_evidence" | "failed" | null;
  citations: Citation[];
  created_at: string;
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${DEV_TOKEN}`);
  if (init.body && !(init.body instanceof Blob)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => undefined);
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function uploadPdf(file: File): Promise<DocumentRecord> {
  if (file.type !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf")) {
    throw new Error("Choose a PDF file.");
  }
  const checksum = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  const sha256 = Array.from(new Uint8Array(checksum), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
  const intent = await request<{
    document_id: string;
    version_id: string;
    upload_url: string;
  }>("/v1/documents/upload-intents", {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      file_name: file.name,
      media_type: "application/pdf",
      size_bytes: file.size,
      sha256,
    }),
  });
  const uploadResponse = await fetch(intent.upload_url, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${DEV_TOKEN}`,
      "Content-Type": "application/pdf",
    },
    body: file,
  });
  if (!uploadResponse.ok) {
    const body = await uploadResponse.json().catch(() => undefined);
    throw new Error(body?.detail ?? `Upload failed (${uploadResponse.status})`);
  }
  await request(`/v1/documents/${intent.document_id}/versions/${intent.version_id}/complete`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      object_version_id: `local:${intent.version_id}`,
      sha256,
    }),
  });

  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    const document = await request<DocumentRecord>(`/v1/documents/${intent.document_id}`);
    if (document.status === "indexed") return document;
    if (document.status === "failed") throw new Error(`Indexing failed for ${document.file_name}.`);
    await new Promise((resolve) => window.setTimeout(resolve, 400));
  }
  throw new Error("Indexing is taking longer than expected. Check the document status and API logs.");
}

export async function createConversation(): Promise<{ conversation_id: string }> {
  return request("/v1/conversations", {
    method: "POST",
    body: JSON.stringify({ title: "Local RAG session" }),
  });
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const page = await request<{ items: DocumentRecord[] }>("/v1/documents");
  return page.items;
}

export async function listMessages(conversationId: string): Promise<ChatMessage[]> {
  const page = await request<{ items: ChatMessage[] }>(
    `/v1/conversations/${conversationId}/messages`,
  );
  return page.items;
}

export async function streamQuestion(
  conversationId: string,
  content: string,
  onDelta: (delta: string) => void,
  onTerminal: (message: ChatMessage) => void,
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/v1/conversations/${conversationId}/messages/stream`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${DEV_TOKEN}`,
        "Content-Type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({ content, document_scope: [] }),
    },
  );
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => undefined);
    throw new Error(body?.detail ?? `Chat request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let terminalMessage: ChatMessage | undefined;
  for (;;) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const eventName = block.match(/^event:\s*(.+)$/m)?.[1];
      const dataLine = block.match(/^data:\s*(.+)$/m)?.[1];
      if (!eventName || !dataLine) continue;
      const data = JSON.parse(dataLine) as {
        event: string;
        event_id: string;
        message_id: string;
        delta?: string;
        content?: string;
        citations?: Citation[];
      };
      if (eventName === "message.delta" && data.delta) onDelta(data.delta);
      if (
        eventName === "message.completed" ||
        eventName === "message.insufficient_evidence"
      ) {
        terminalMessage = {
          message_id: data.message_id,
          conversation_id: conversationId,
          role: "assistant",
          content: data.content ?? "",
          status:
            eventName === "message.completed" ? "completed" : "insufficient_evidence",
          citations: data.citations ?? [],
          created_at: new Date().toISOString(),
        };
        onTerminal(terminalMessage);
      }
      if (eventName === "message.error") {
        throw new Error("The chat stream ended with an API error.");
      }
    }
    if (done) break;
  }
  if (!terminalMessage) throw new Error("The chat stream ended before a terminal event.");
}
