# Contracts Package

This package is the source of truth for public API schemas, transport DTOs, versioned domain-event schemas, and serializable RAG workflow state.

- `..\..\docs\contracts\openapi.yaml` defines the HTTP contract.
- `python\rag_contracts\` contains Pydantic v2 transport/workflow models.
- `..\..\docs\contracts\events.schema.json` defines event envelopes and payloads.
- `..\..\docs\contracts\domain-model.md` explains persistent entities and lifecycle.

Contract models may depend on Pydantic at the serialization boundary. Domain entities and application ports must not depend on this package's transport models or on provider SDKs. Generated TypeScript clients should be derived from OpenAPI rather than hand-maintained copies.

This is contract scaffolding only; it does not implement API handlers or persistence.

