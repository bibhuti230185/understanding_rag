import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ChatMessage,
  DEV_TOKEN,
  DocumentRecord,
  createConversation,
  listDocuments,
  listMessages,
  streamQuestion,
  uploadPdf,
} from "./api";

export default function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listDocuments().then(setDocuments).catch((reason: Error) => setError(reason.message));
  }, []);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileInput.current?.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(undefined);
    try {
      const indexed = await uploadPdf(file);
      setDocuments((current) => [
        indexed,
        ...current.filter((item) => item.document_id !== indexed.document_id),
      ]);
      if (fileInput.current) fileInput.current.value = "";
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "PDF upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(undefined);
    try {
      let activeConversation = conversationId;
      if (!activeConversation) {
        const created = await createConversation();
        activeConversation = created.conversation_id;
        setConversationId(activeConversation);
      }
      const history = await listMessages(activeConversation);
      setMessages(history);
      const userMessage: ChatMessage = {
        message_id: crypto.randomUUID(),
        conversation_id: activeConversation,
        role: "user",
        content: text,
        citations: [],
        created_at: new Date().toISOString(),
      };
      const pendingId = crypto.randomUUID();
      const pending: ChatMessage = {
        message_id: pendingId,
        conversation_id: activeConversation,
        role: "assistant",
        content: "",
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((current) => [...current, userMessage, pending]);
      setQuestion("");
      await streamQuestion(
        activeConversation,
        text,
        (delta) =>
          setMessages((current) =>
            current.map((item) =>
              item.message_id === pendingId
                ? { ...item, content: item.content + delta }
                : item,
            ),
          ),
        (terminal) =>
          setMessages((current) =>
            current.map((item) =>
              item.message_id === pendingId ? terminal : item,
            ),
          ),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The question could not be answered.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">RAG LUCID AI · PHASE 4</p>
          <h1>Ask your documents</h1>
        </div>
        <div className="identity" title="Development identity only">
          <span className="status-dot" />
          Local demo · {DEV_TOKEN === "local-dev-token" ? "default token" : "configured token"}
        </div>
      </header>

      <section className="layout">
        <aside className="panel library">
          <div className="section-heading">
            <div>
              <p className="eyebrow">YOUR LIBRARY</p>
              <h2>Documents</h2>
            </div>
            <span className="count">{documents.length}</span>
          </div>
          <form className="upload-box" onSubmit={handleUpload}>
            <label htmlFor="pdf-file">Add a PDF</label>
            <input id="pdf-file" ref={fileInput} type="file" accept="application/pdf,.pdf" />
            <button type="submit" className="button secondary" disabled={busy}>
              {busy ? "Working…" : "Upload and index"}
            </button>
            <p className="muted">PDF only · stored locally · mock AI</p>
          </form>
          <div className="document-list">
            {documents.length === 0 ? (
              <p className="empty">Your indexed PDFs will appear here.</p>
            ) : (
              documents.map((document) => (
                <article className="document-row" key={document.document_id}>
                  <span className="pdf-icon">PDF</span>
                  <div className="document-meta">
                    <strong title={document.file_name}>{document.file_name}</strong>
                    <span>{document.status}</span>
                  </div>
                  <span className={`status-tag ${document.status}`}>{document.status}</span>
                </article>
              ))
            )}
          </div>
          <p className="security-note">
            Local development identity only. Do not expose this app or API to an untrusted network.
          </p>
        </aside>

        <section className="panel chat">
          <div className="section-heading">
            <div>
              <p className="eyebrow">GROUNDED ANSWERS</p>
              <h2>Conversation</h2>
            </div>
            <button
              className="text-button"
              onClick={() => {
                setConversationId(undefined);
                setMessages([]);
                setError(undefined);
              }}
            >
              New chat
            </button>
          </div>
          <div className="messages">
            {messages.length === 0 ? (
              <div className="welcome">
                <div className="spark">✳</div>
                <h3>Start with a question</h3>
                <p>Upload a PDF, then ask about its contents. Answers quote retrieved evidence.</p>
                {documents.filter((document) => document.status === "indexed").length === 0 && (
                  <span className="hint">Add an indexed PDF to begin.</span>
                )}
              </div>
            ) : (
              messages.map((message) => (
                <article className={`message ${message.role}`} key={message.message_id}>
                  <span className="message-label">
                    {message.role === "user" ? "YOU" : "RAG ASSISTANT"}
                  </span>
                  <p>{message.content || (busy ? "Finding evidence…" : "")}</p>
                  {message.citations.length > 0 && (
                    <div className="citations">
                      <span className="citation-heading">SOURCES</span>
                      {message.citations.map((citation) => {
                        const source = documents.find(
                          (document) => document.document_id === citation.document_id,
                        );
                        return (
                          <div className="citation" key={citation.chunk_id}>
                            <strong>{source?.file_name ?? "Source document"}</strong>
                            {citation.page_number && <span> · page {citation.page_number}</span>}
                            {citation.excerpt && <blockquote>{citation.excerpt}</blockquote>}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {message.status === "insufficient_evidence" && (
                    <span className="hint">No supporting evidence was found.</span>
                  )}
                </article>
              ))
            )}
          </div>
          {error && <div className="error-banner" role="alert">{error}</div>}
          <form className="composer" onSubmit={handleAsk}>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about your PDFs…"
              maxLength={12000}
              disabled={busy}
            />
            <button type="submit" className="button primary" disabled={busy || !question.trim()}>
              Ask <span aria-hidden="true">↗</span>
            </button>
          </form>
          <p className="footer-note">Mock embeddings and evidence-copy responses · not production AI</p>
        </section>
      </section>
    </main>
  );
}
