# Research and Design Decisions

**Feature**: Product Framing, LLD Contracts, and Repository Structure  
**Date**: 2026-11-17  
**Source**: `RAG_Lucid_AI_Arch.docx` phases 0, 2, and 3, plus Phase 1 artifacts under `docs\architecture\`

## Decisions

### Provisional SLOs

- **Decision**: Record low-volume MVP planning hypotheses in `docs\product\product-brief.md`: 99.5% API availability, p95 retrieval at 1.5 seconds, p95 time to first validated answer token at 3 seconds, 95% of eligible documents indexed within 5 minutes, at least 95% citation correctness, and $0.15 average provider cost per defined 10-turn conversation.
- **Rationale**: Phase 0 explicitly requests initial SLOs and measurable success metrics. Without a known provider, workload, or file-size envelope, targets must remain provisional and include measurement definitions.
- **Alternatives considered**: Omit all numbers; rejected because the source phase requests initial targets. Treat the values as production guarantees; rejected because the required baseline and stakeholder approval do not exist.

### Contract format

- **Decision**: Use OpenAPI 3.1 for HTTP paths/schemas, Pydantic v2 models for Python transport and serializable workflow payloads, and JSON Schema 2020-12 for internal document lifecycle events.
- **Rationale**: These formats cover browser/API compatibility, Python validation, and language-neutral worker events while keeping framework concerns at boundaries.
- **Alternatives considered**: Hand-maintained frontend and backend schema copies; rejected because they drift. Expose framework/SDK types in the API contract; rejected because it couples clients and core logic to implementation details.

### API interaction model

- **Decision**: Version REST endpoints under `/v1`, use RFC 9457-style `application/problem+json` errors, SSE for chat events, and opaque cursor pagination.
- **Rationale**: The product requires browser upload/chat workflows, streaming, stable errors, and pagination; REST/SSE fit the stated client and Python API architecture.
- **Alternatives considered**: WebSockets for one-way answer streaming; deferred because the initial chat stream does not require bidirectional event transport. Offset pagination; rejected for unstable ordering under concurrent document/message writes.

### Tenant authorization

- **Decision**: Resolve tenant/user/role from a validated token plus server-side active membership; apply resource ACL checks to every document, conversation, evaluation, vector, cache, and deletion operation.
- **Rationale**: Client tenant identifiers and model output cannot establish authority. Resource existence may be concealed with a consistent 404 policy to limit identifier oracles.
- **Alternatives considered**: Trust a tenant header/body field; rejected as an insecure authority source. Put authorization only in prompt instructions; rejected because model output cannot enforce access control.

### Repository structure

- **Decision**: Create the source roadmap's monorepo boundaries as README ownership markers and place OpenAPI/Pydantic/event contracts in `packages/contracts`.
- **Rationale**: Contributors can navigate and build the vertical slice next without creating placeholder services, dependencies, cloud resources, or CI behavior before their commands and requirements are known.
- **Alternatives considered**: Generate all runtime app files/manifests now; rejected because Phase 3 defines structure and Phase 4 owns the first executable vertical slice. Leave empty directories; rejected because ownership and phase status would be unclear.

## Open Decisions

- Confirm supported upload limits and parser timeouts; the initial SLO benchmark assumes a file up to 25 MB and 100 pages/slides, which is not a production policy.
- Confirm role/ownership policy for normal-user uploads and deletion, platform break-glass, and evaluator access.
- Confirm identity provider/federation, model/embedding provider, model versions, data-processing terms, and private networking needs.
- Define idempotency retention duration, cursor signing/expiry keys, deletion SLA, audit/telemetry retention, and provider trace payload policy.
- Approve API SLOs, traffic profile, load-test envelope, cost budget, compliance, data residency, RPO/RTO, and AWS account/region topology.

