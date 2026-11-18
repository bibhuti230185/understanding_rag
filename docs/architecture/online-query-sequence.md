# Online Query and Cited Streaming Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as React chat client
    participant API as FastAPI API
    participant IdP as Cognito / OIDC
    participant DB as PostgreSQL
    participant Cache as Redis
    participant Graph as LangGraph query workflow
    participant Embed as Embedding provider
    participant Vector as VectorStore port / ChromaDB
    participant Rank as Reranker / context compression
    participant LLM as Hosted LLM
    participant Obs as OpenTelemetry / CloudWatch / Langfuse

    User->>Web: Ask question in conversation
    Web->>IdP: Obtain/refresh signed identity token
    IdP-->>Web: Signed identity token
    Web->>API: POST question with conversation ID and token
    API->>API: Verify token and resolve tenant, user, and role
    API->>DB: Authorize conversation and load permitted scope
    DB-->>API: Tenant-scoped conversation and policy
    API->>DB: Persist user message and request/correlation IDs
    API->>Graph: Start workflow with verified tenant/user context
    Graph->>Cache: Lookup tenant + normalized query + filters + index version
    alt Authorized cache hit
        Cache-->>Graph: Candidate result set
    else Cache miss
        Graph->>Embed: Embed query
        Embed-->>Graph: Query vector
        Graph->>Vector: Search with mandatory tenant/document ACL filters
        Vector-->>Graph: Candidate chunks and source metadata
        Graph->>Rank: Rerank and compress authorized evidence
        Rank-->>Graph: Bounded evidence context
        Graph->>Cache: Store safe result using tenant-scoped key and TTL
    end
    Graph->>Graph: Build prompt and mark retrieved text as untrusted evidence
    Graph->>LLM: Generate answer with citation requirements
    Note over Graph,LLM: Generate a draft and keep token deltas server-side until grounding and citation checks finish
    loop Answer tokens
        LLM-->>Graph: Draft token/event
        Graph->>Graph: Buffer draft and collect citation references
    end
    Graph->>Graph: Validate citations against retrieved source IDs
    alt Sufficient authorized evidence and valid citations
        Graph-->>API: Validated answer, citations, usage, and trace metadata
    else No sufficient evidence or invalid citations
        Graph-->>API: Insufficient-evidence response and discard draft
    end
    API->>DB: Persist assistant message and citations
    API->>Obs: Emit redacted trace, latency, usage, model, and outcome
    alt Validated answer
        loop Validated answer chunks
            API-->>Web: SSE answer delta
            Web-->>User: Render verified answer chunk
        end
    else Insufficient evidence
        API-->>Web: SSE insufficient-evidence event
        Web-->>User: Show no-evidence response
    end
    API-->>Web: SSE completion with citations and final status
    Web-->>User: Show source drill-down and feedback controls
    User->>Web: Submit thumbs-up/down feedback
    Web->>API: Feedback for authorized conversation/message
    API->>DB: Persist tenant-scoped feedback
    API->>Obs: Associate feedback with trace/prompt version
```

## Query Safety and Failure Behavior

- Verify conversation ownership and derive tenant scope before reading cache or retrieval results.
- Apply tenant and document authorization filters in the vector-store adapter; do not rely on prompt instructions or client-provided filters for access control.
- Cache keys include tenant, normalized query, authorized filters, index version, and retrieval parameters. Unsafe or permission-sensitive generated answers are not shared across users or tenants.
- Retrieved chunks are labeled as untrusted evidence. The system prompt and policy are kept separate; document text cannot authorize tools, change policy, or request secrets.
- Citations are checked against the retrieved set before finalization. If evidence is insufficient, citations are invalid, or the provider fails, return a clear bounded failure/insufficient-evidence event rather than inventing an answer.
- Draft tokens are not exposed to the browser until evidence and citation checks pass. The UI can show progress during generation; validated answer chunks are then delivered over SSE. This favors evidence safety over minimum time-to-first-answer-token.
- Cancellation, timeout, provider throttling, vector-store unavailability, and cache failure are observable outcomes. A cache or telemetry outage must not bypass authorization.
