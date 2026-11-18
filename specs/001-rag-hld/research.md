# Research and Design Decisions

**Feature**: Phase 1 RAG HLD and System Architecture  
**Date**: 2026-11-17

This phase is constrained by the user-provided architecture roadmap in `RAG_Lucid_AI_Arch.docx`. No external service sizing, compliance, or regional availability research was possible or required to produce the requested HLD. Items dependent on those inputs are explicitly deferred rather than guessed.

## Decisions

### Modular API plus ingestion worker

- **Decision**: Keep user-facing use cases in a modular FastAPI application and run ingestion in a separate worker deployment.
- **Rationale**: The initial system remains understandable as a modular monolith, while parsing and embedding jobs need independent concurrency, retry, and resource controls.
- **Alternatives considered**: Split every bounded context into a microservice; rejected for the initial release because it adds deployment and cross-service coordination without validated independent scaling needs. Run ingestion synchronously in API requests; rejected because file parsing and embedding are long-running and retryable.

### S3 and SQS for ingestion handoff

- **Decision**: Store originals in S3, enqueue verified upload completions to SQS, retry transient failures, and route exhausted work to a DLQ.
- **Rationale**: Object storage and queue lifecycles are separate; an asynchronous handoff decouples upload latency from parsing and embedding.
- **Alternatives considered**: Store file bytes in PostgreSQL; rejected because the source roadmap separates document storage from metadata. Run a direct API-to-worker call; rejected because it couples user requests to long-running work and loses queue-based recovery.

### Application-owned vector-store port

- **Decision**: Start with ChromaDB behind a `VectorStore` port owned by the application/domain boundary.
- **Rationale**: ChromaDB is explicitly the hands-on first-release choice in the source roadmap. The interface boundary makes later provider migration possible without leaking SDK and schema details into core use cases.
- **Alternatives considered**: Couple retrieval code directly to ChromaDB; rejected because it makes migration and isolated testing harder. Select a managed vector database now; deferred until workload, tenancy, availability, and cost requirements are known.

### Identity and tenant enforcement

- **Decision**: Show Cognito as the initial identity provider; derive tenant and roles from verified identity claims and enforce tenant authorization in API use cases and data-access adapters.
- **Rationale**: The source roadmap calls for Cognito or enterprise identity and multi-tenant isolation. A signed identity is the trusted source for tenant scope; request-body tenant IDs are not.
- **Alternatives considered**: Trust the browser's tenant parameter; rejected as insecure. Hard-code a single tenant; rejected because multi-tenancy is a target property.

### Metadata, cache, and telemetry ownership

- **Decision**: PostgreSQL is the source of truth; Redis is optional and disposable; operational logs/metrics/traces go to CloudWatch/OpenTelemetry, while Langfuse supports LLM-specific tracing and evaluations.
- **Rationale**: This matches the source roadmap and keeps correctness independent of cache availability. Telemetry must avoid unnecessary prompt, document, or PII capture.
- **Alternatives considered**: Treat cache as authoritative; rejected because eviction/outage must not change authorization or durable conversation state. Record raw prompts and documents in every trace; rejected because it increases privacy and data-exposure risk.

## Unresolved Inputs (Deferred)

- Tenant and document volumes, request concurrency, latency and availability SLOs.
- Required compliance regimes, data residency, retention/deletion SLAs, and audit retention.
- LLM and embedding providers, model fallback policy, and provider egress restrictions.
- Production ChromaDB persistence/scaling design versus migration to a managed vector service.
- AWS account/region topology, budget, RPO/RTO, and DR strategy.

