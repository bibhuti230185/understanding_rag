# Implementation Plan: Product Framing, LLD Contracts, and Repository Structure

**Branch**: `002-product-contracts-structure` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Phases 0, 2, and 3 of `RAG_Lucid_AI_Arch.docx`, building on Phase 1 in `docs\architecture\`

## Summary

Complete the product framing and assumptions, propose measurable MVP SLOs, define the API/domain/event/RAG-state contracts, and scaffold the target monorepo. The API contract is OpenAPI 3.1 with matching Pydantic v2 DTOs and versioned event schemas. The repository gets structural READMEs and a canonical layout document, but no application use cases or AWS resources.

## Technical Context

**Language/Version**: Python 3.11+ for the future API/worker; TypeScript for the future React client. Python version is provisional and must be fixed in the Phase 4 build setup.

**Primary Dependencies**: OpenAPI 3.1; Pydantic v2 for API contract models; Mermaid/Markdown architecture documentation.

**Storage**: Contracted target is S3 for files, PostgreSQL for metadata/conversations/audit, Redis for disposable cache, and ChromaDB behind a vector-store port. Nothing is provisioned in this phase.

**Testing**: Parse OpenAPI and JSON Schema; validate Pydantic examples and negative cases; verify linked docs and scaffold paths. Existing environment has Python 3.13 and Pydantic 2.14.3.

**Target Platform**: AWS target architecture; local developer environments are platform-independent.

**Project Type**: Monorepo scaffold for a web application and Python API/worker, plus contract package and documentation.

**Performance Goals**: Provisional Phase 0 targets: 99.5% monthly API availability; p95 retrieval ≤1.5 s; p95 time-to-first-validated-answer-token ≤3 s; 95% of eligible documents indexed within 5 minutes after upload completion; ≥95% citation correctness on a versioned evaluation set; average model cost ≤$0.15 per standard 10-turn conversation. These are hypotheses, not commitments, pending benchmark definition and workload/provider measurement.

**Constraints**: Tenant scope comes only from validated identity and server-side membership; no cross-tenant cache/retrieval sharing; source text is untrusted; errors are explicit; durable metadata and vector providers are behind ports; no raw secrets/content in queue or ordinary telemetry.

**Scale/Scope**: Initial multi-tenant MVP; four roles; upload PDF/DOCX/PPTX, asynchronous indexing, cited streaming chat, feedback, document deletion, and evaluator-run workflows. Exact traffic, document-size envelope, regulatory regime, model provider, and retention are open.

## Constitution Check

`.specify/memory/constitution.md` is an unfilled template, not ratified governance. The feature therefore follows explicit constraints from the product roadmap and Phase 1: least privilege, tenant-scoped access, untrusted-document handling, idempotent async work, provider isolation, and observability with data minimization.

### Post-Design Check

- **Product scope**: Pass. The brief separates MVP from production extensions and interview-only outcomes.
- **Contract-first**: Pass. OpenAPI, Pydantic DTOs, entity definitions, events, and workflow state are defined before service code.
- **Tenant isolation**: Pass. The public contract never treats a client tenant identifier as authoritative; tenant scope is a server-derived security context.
- **Provider independence**: Pass. Contracts use application-owned IDs/value objects and hide SDK-specific types.
- **Structure**: Pass. The scaffold maps each package and app to a responsibility and marks code as not yet implemented.
- **Deferred decisions**: Workload, provider, SLO approval, compliance, data retention, and DR remain explicitly unresolved.

## Key Decisions

1. **API**: REST `/v1`, JSON requests/responses, SSE for chat events; cursor pagination with stable opaque cursors.
2. **Errors**: RFC 9457 problem details with stable application `code`, `correlation_id`, and field-level validation details.
3. **Identity**: Authenticated user claims plus server-side tenant membership determine tenant and role. Resource ownership/ACL checks are applied for every operation.
4. **Job state**: `queued -> processing -> indexed | failed | deleted`; `failed -> queued` only through an explicit retry action. `deleted` is terminal for that immutable document version.
5. **Idempotency**: Client upload/evaluation operations use `Idempotency-Key`; workers deduplicate by tenant, document version, operation, and index configuration. Key/payload mismatch returns conflict.
6. **Events**: CloudEvents-style envelope with schema version, event ID, tenant, time, correlation ID, and W3C trace context. Event payloads contain identifiers, not file bytes or credentials.
7. **Monorepo**: One web app, one modular API, one worker, shared domain/application/RAG/ingestion/infrastructure/observability/evaluation packages, contract and test packages, Terraform environments, and documentation.
8. **Contracts package**: Pydantic is restricted to transport/state serialization at the contract boundary; domain entities and ports remain framework-neutral.

## Project Structure

```text
apps/
  web/                 # React + TypeScript client
  api/                 # FastAPI HTTP application
  worker/              # asynchronous ingestion and maintenance
packages/
  contracts/           # OpenAPI, Pydantic DTOs, event schemas
  domain/              # entities, policies, ports, value objects
  application/         # use cases and orchestration
  rag/                 # retrieval, prompting, citations, guardrails
  ingestion/           # parsing, cleaning, chunking, metadata
  infrastructure/      # PostgreSQL, Redis, S3, SQS, Chroma, LLM, Langfuse adapters
  observability/       # logging, tracing, metrics, cost accounting
  evals/               # datasets, evaluators, regression thresholds
tests/
  unit/ integration/ contract/ e2e/ evaluation/
infra/terraform/
  modules/
  environments/dev/ environments/staging/ environments/prod/
docs/
  product/ contracts/ architecture/ adr/ runbooks/ interview-notes/
.github/workflows/
```

**Structure Decision**: The repository README files and contract package are scaffolding and interface artifacts. Executable web/API/worker functionality, dependency manifests for those apps, Terraform resources, CI pipelines, and runtime configuration are later-phase work.

## Complexity Tracking

No additional deployable service is introduced. Pydantic is used only for the requested API contract models; no framework or cloud SDK is added to domain/application packages.

