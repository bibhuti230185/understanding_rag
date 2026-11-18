# Monorepo Structure and Ownership

The repository is a single product monorepo. The API starts as a modular monolith; the ingestion worker is the only separate application in the MVP. Package and app READMEs created in Phase 3 are ownership markers, not evidence that runtime code is implemented.

```text
rag-platform/
|-- apps/
|   |-- web/                 # React + TypeScript client
|   |-- api/                 # FastAPI HTTP application
|   `-- worker/              # asynchronous ingestion and maintenance
|-- packages/
|   |-- contracts/           # OpenAPI, Pydantic DTOs, event schemas
|   |-- domain/              # entities, policies, ports, value objects
|   |-- application/         # use cases and orchestration
|   |-- rag/                 # retrieval, prompting, citations, guardrails
|   |-- ingestion/           # parsing, cleaning, chunking, metadata
|   |-- infrastructure/      # DB, Redis, S3/SQS, Chroma, LLM, Langfuse adapters
|   |-- observability/       # logging, tracing, metrics, cost accounting
|   `-- evals/               # datasets, evaluators, regression thresholds
|-- tests/
|   |-- unit/
|   |-- integration/
|   |-- contract/
|   |-- e2e/
|   `-- evaluation/
|-- infra/terraform/
|   |-- modules/
|   `-- environments/{dev,staging,prod}/
|-- docs/
|   |-- product/ contracts/ architecture/ adr/ runbooks/ interview-notes/
`-- .github/workflows/
```

## Application Modules

### Web: `apps/web/src/features/`

`auth`, `documents`, `ingestion-status`, `chat`, `citations`, `feedback`, `admin`, and `evaluations`. Shared `api-client` is generated from OpenAPI; `streaming-client` handles the SSE contract. Every feature includes explicit loading, empty, error, and authorization-denied states.

### API: `apps/api/src/rag_platform_api/`

`auth_tenant`, `documents`, `ingestion`, `retrieval`, `chat`, `conversations`, `feedback`, `evaluations`, `health`, and `admin`. Route handlers translate HTTP contracts into application use cases; they do not contain business logic or SDK-specific persistence code.

### Worker: `apps/worker/src/rag_platform_worker/`

Queue consumers and maintenance entrypoints for `ingestion`, `deletion`, `reindexing`, and `reconciliation`. Worker messages are versioned identifiers; handlers are idempotent and call application use cases.

## Package Dependency Direction

```text
apps -> packages/application -> packages/domain
apps -> packages/contracts (transport mapping only)
packages/application -> domain ports
packages/infrastructure -> domain ports + provider SDKs
packages/rag / packages/ingestion -> domain abstractions
packages/observability -> telemetry adapters
packages/evals -> contracts and application test interfaces
```

- `domain` contains framework/provider-neutral entities, policies, ports, and value objects.
- `application` orchestrates use cases and depends on domain ports.
- `infrastructure` implements ports for PostgreSQL, Redis, S3, SQS, ChromaDB, hosted models, and Langfuse.
- `contracts` contains Pydantic transport DTOs, OpenAPI source, and serializable event/workflow schemas. Mapping isolates these from domain entities.
- No layer above an adapter imports ChromaDB, LangChain/LangGraph, Langfuse, Redis, or AWS SDK types.

## Test Layers

- `unit`: pure policies, chunking, citation mapping, cache-key construction, and state transition logic.
- `integration`: PostgreSQL, Redis, object storage, queue, and vector-store adapters.
- `contract`: OpenAPI/Pydantic/schema compatibility and generated frontend-client checks.
- `e2e`: upload, status, chat, citations, feedback, and deletion journeys.
- `evaluation`: retrieval/answer golden-set regression and quality thresholds.

## Phase Boundaries

- Phase 3 creates the layout and ownership markers, plus the Phase 2 contract package.
- Phase 4 introduces build manifests and one vertical slice.
- Terraform module directories remain documentation-only until infrastructure planning and approval.
- CI workflow source files are deferred until the runtime build/test commands are established.

