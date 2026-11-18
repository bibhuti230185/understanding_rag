# ADR-0003: S3 Uploads with SQS-Driven Ingestion

- **Status**: Accepted for initial architecture
- **Date**: 2026-11-17
- **Context**: PDF, DOCX, and PPTX parsing, chunking, and embedding are variable-duration tasks. Upload latency must not depend on successful completion of ingestion, and jobs need retry and dead-letter handling.

## Decision

Store original files in a private S3 quarantine location using short-lived, object-scoped upload authorization. After server-side completion verification, enqueue a document-version identifier in SQS. A separately deployed worker validates/scans and processes the exact object version, persists lifecycle state in PostgreSQL, writes tenant/document-scoped vectors through the vector-store port, and acknowledges only after terminal success or failure handling. Use bounded retries and a DLQ.

## Consequences

- Upload acknowledgment is fast and independent of parsing/model-provider latency.
- Queue delivery is at least once; worker operations must be idempotent and use stable document-version identity.
- The design needs status visibility, retry/DLQ alarms, operator replay controls, and reconciliation for partial writes.
- Queue messages should contain identifiers and correlation data, not file contents, secrets, or authorization tokens.
- Deletion and re-indexing must coordinate S3 object versions, job state, metadata, vector records, and caches.

## Alternatives Considered

- **Synchronous processing inside the upload request**: Rejected; long-running work ties up web capacity and gives poor retry/recovery semantics.
- **Direct API-to-worker invocation without a durable queue**: Rejected; it couples deployments and provides weaker buffering, retry, and poison-message isolation.
- **Store raw files in PostgreSQL**: Rejected; the source roadmap separates object storage from metadata and large binary payloads.

