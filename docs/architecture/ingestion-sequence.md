# Ingestion Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as React client
    participant API as FastAPI API
    participant IdP as Cognito / OIDC
    participant DB as PostgreSQL
    participant S3 as S3 quarantine
    participant Q as SQS + DLQ
    participant Worker as Ingestion worker
    participant Scan as File validation / malware scan
    participant Parser as Parser / cleaner / chunker
    participant Embed as Embedding provider
    participant Vector as VectorStore port / ChromaDB
    participant Obs as OpenTelemetry / CloudWatch / Langfuse
    participant DLQ as SQS dead-letter queue

    User->>Web: Select PDF, DOCX, or PPTX
    Web->>IdP: Authenticate
    IdP-->>Web: Signed identity token
    Web->>API: Request upload authorization (token, filename, size, media type)
    API->>API: Verify identity and resolve tenant and role
    API->>API: Validate allowed type, size, and upload policy
    API->>DB: Create document version and queued upload record
    API-->>Web: Document ID + short-lived single-object upload URL
    Web->>S3: PUT original to tenant-scoped quarantine key
    S3-->>Web: Upload result
    Web->>API: Complete upload (document ID, object version/checksum)
    API->>API: Re-authorize tenant and validate completion/idempotency
    API->>S3: Verify object existence, size, metadata, and checksum
    API->>Q: Enqueue document-version job (identifier only)
    API->>DB: Persist job queued state and idempotency key
    API-->>Web: Accepted - return ingestion status resource

    Q->>Worker: Deliver job (at-least-once)
    Worker->>DB: Claim job using idempotent transition
    Worker->>S3: Read staged object by exact version
    Worker->>Scan: MIME/content validation and malware scan
    alt Rejected, malformed, or infected
        Scan-->>Worker: Rejection reason
        Worker->>DB: Mark document/job failed or quarantined
        Worker->>Obs: Emit failure category and correlation IDs
    else Accepted
        Scan-->>Worker: Clean file
        Worker->>Parser: Parse, clean, chunk, and attach source locations
        Parser-->>Worker: Chunks and document metadata
        Worker->>Embed: Create embeddings with model/version metadata
        Embed-->>Worker: Vectors
        Worker->>Vector: Upsert using tenant/document/version metadata
        Worker->>DB: Persist index version and mark job/document indexed
        Worker->>Obs: Emit duration, counts, model/version, and outcome
    end
    Worker-->>Q: Acknowledge successful or terminally handled job
    Worker->>Q: Leave transient failure unacknowledged
    Q->>Worker: Redeliver after visibility timeout (bounded backoff)
    Q->>DLQ: Move message after max receives
    User->>Web: Check ingestion status
    Web->>API: Get status (authenticated)
    API->>DB: Read tenant-authorized status
    API-->>Web: Queued / processing / indexed / failed / quarantined
```

## Reliability and Lifecycle Notes

- SQS delivery is at least once; the worker uses a stable tenant/document/version idempotency identity and upserts rather than blindly appending chunks.
- A job becomes visible as indexed only after vector writes and durable metadata updates are confirmed. If those operations cannot be made atomic, use a recoverable index-version state and reconciliation job.
- Retries are bounded and apply only to transient faults. Invalid, infected, unsupported, or malformed inputs are terminal and must not be retried indefinitely.
- DLQ messages contain identifiers and error categories; replay requires operator authorization and uses the same idempotency identity.
- Source object version/checksum is retained with the document version so retries and re-indexing use the same bytes.
- Deletion marks the document unavailable immediately, cancels or invalidates in-flight jobs, removes vector records and cache entries, and applies the configured S3/metadata retention policy. The exact deletion SLA is deferred.
