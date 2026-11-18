# RAG Workflow State Contract

The query workflow receives a server-constructed state after authentication, tenant membership validation, conversation authorization, and input validation. The browser cannot provide or override `tenant_id`, `user_id`, authorization filters, or safety decisions.

| Field | Type | Producer | Contract |
|---|---|---|---|
| `question` | string | API | Required, 1-12,000 characters; user content is untrusted |
| `tenant_id` | UUID | Auth/tenant adapter | Derived from verified claims and active membership |
| `user_id` | UUID | Identity adapter | Derived from verified subject mapping |
| `conversation_id` | UUID | API | Must be authorized for the principal |
| `message_id` | UUID | Application | Stable ID for retries and message persistence |
| `rewritten_queries` | string[] | Query workflow | Derived variants; each inherits original tenant/security scope |
| `retrieved_documents` | RetrievedChunk[] | VectorStore adapter | Only authorized chunks; includes score and source location |
| `reranked_context` | RetrievedChunk[] | Reranker/context step | Subset/reordering of authorized retrieved evidence; bounded before prompt construction |
| `answer` | string or null | Generation step | Draft remains server-side until grounding/citation validation |
| `citations` | Citation[] | Citation validator | Every reference resolves to a retrieved chunk and authorized document version |
| `safety_flags` | string[] | Guardrail steps | Machine-readable outcomes; not a substitute for authorization checks |
| `token_usage` | input/output token counts or null | Model adapter | Non-negative counts from provider usage or explicitly marked estimate |
| `cost_usd` | decimal or null | Cost accounting | Non-negative; currency is USD in initial contract; identify estimate vs provider-reported cost in telemetry |

## Workflow Invariants

1. Construct identity and authorization scope before entering the graph; never infer tenant access from model output.
2. Authorization filters are mandatory at the vector-store port even when the question names a document.
3. Cache keys and hits preserve tenant, document scope, index version, and retrieval configuration.
4. Retrieved content and rewritten queries are data, not instructions. The system policy is never read from a document.
5. The graph may produce a server-side draft; only validated answer text and citations are emitted to the client.
6. Insufficient evidence is a successful, explicit terminal outcome with no unsupported answer. Provider/dependency errors are terminal error events.
7. Graph retries are bounded and use the same message/idempotency identity to prevent duplicate conversation messages.
8. Framework graph state/checkpoints are behind an adapter. No graph runtime class is part of the domain contract.

## SSE Event Contract

Each event is encoded as `id: <event_id>`, `event: <event_type>`, and one-line JSON `data:`. Event payload schemas are represented by `SseProgress`, `SseDelta`, `SseCompleted`, `SseInsufficientEvidence`, and `SseError` Pydantic models.

- `message.progress`: safe stage notification; no model draft text.
- `message.delta`: validated answer text only. If the chosen generation policy cannot validate incrementally, buffer until the final citation check and then emit answer chunks.
- `message.completed`: complete answer, verified citations, usage, and cost.
- `message.insufficient_evidence`: explicit no-evidence outcome and optional valid citations.
- `message.error`: RFC 9457-style problem; no stack trace, prompt, or provider credential.

The stream is incomplete unless a terminal `message.completed`, `message.insufficient_evidence`, or `message.error` is received. Disconnect recovery by `Last-Event-ID` is optional and must not rerun generation as a new logical message.

