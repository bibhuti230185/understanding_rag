# Contract Artifacts

- `openapi.yaml`: versioned public HTTP API.
- `events.schema.json`: JSON Schema for internal document lifecycle events.
- `domain-model.md`: entity relationships and ingestion state transitions.
- `rag-state.md`: serializable RAG workflow state and SSE event behavior.
- `idempotency-and-tracing.md`: request/job deduplication and trace propagation.
- `authorization-and-pagination.md`: tenant scoping, role policy, filters, and cursors.

The public API uses tenant scope resolved by the server, not a caller-provided tenant ID. These files are design contracts; implementation adapters are built in later phases.

