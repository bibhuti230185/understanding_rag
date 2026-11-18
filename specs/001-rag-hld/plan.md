# Implementation Plan: Phase 1 RAG HLD and System Architecture

**Branch**: `001-rag-hld` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Phase 1 architecture requirements from `RAG_Lucid_AI_Arch.docx`

## Summary

Create a reviewable HLD package for the multi-tenant document knowledge assistant. Use a React browser client, AWS edge and identity controls, a modular FastAPI application, a separately deployed asynchronous ingestion worker, PostgreSQL metadata, Redis as an optional cache, and ChromaDB behind an application-owned vector-store port. Document the context, container, ingestion sequence, online query sequence, deployment, threat model, and architecture decisions as Mermaid-enabled Markdown. This phase produces architecture documentation only.

## Technical Context

**Language/Version**: Not applicable; documentation-only feature.

**Primary Dependencies**: GitHub Spec Kit feature templates; Markdown; Mermaid diagrams.

**Storage**: Repository documentation only. The architecture describes S3, PostgreSQL, Redis, SQS, and ChromaDB as future runtime components; none are provisioned in this phase.

**Testing**: Manual traceability review against FR-001 through FR-012; check all Mermaid blocks and verify the described flows match the source roadmap.

**Target Platform**: Architecture target is AWS; documentation is platform-independent.

**Project Type**: Architecture documentation package.

**Performance Goals**: No runtime performance target is established in this phase. Product SLOs are deferred pending workload and business requirements.

**Constraints**: Keep scope to HLD, security boundaries, failure behavior, and ADRs. Do not implement application code, cloud resources, detailed API schemas, or logical database schemas. Tenant identity and scope must be authoritative and enforced at every data access boundary. Retrieved document content is untrusted input.

**Scale/Scope**: Multi-tenant document assistant; PDF, DOCX, and PPTX ingestion; cited streaming answers; roles include tenant administrator, user, evaluator, and platform operator. Exact tenant, document, traffic, and availability targets remain undecided.

## Constitution Check

The existing `.specify/memory/constitution.md` contains unfilled template placeholders and no ratified project principles; it cannot be treated as an enforceable project constitution. This plan therefore records explicit feature constraints instead: tenant isolation, least privilege, untrusted-content handling, observable failure paths, and an application-owned vector-store boundary. No code or deployment scope is introduced.

### Post-Design Check

- **Scope**: Pass. The planned artifacts are HLD documentation only.
- **Security boundary**: Pass. Tenant scope derives from verified identity and is applied at metadata, vector, cache, and lifecycle operations.
- **Migration boundary**: Pass. ChromaDB is an adapter behind a domain/application-owned port.
- **Operational clarity**: Pass. Queue retries/DLQ, storage ownership, and telemetry are represented.
- **Deferred decisions**: SLO values, compliance/retention, exact model provider, and regional DR are explicitly left for later requirements work.

## Design Decisions

1. Use a modular monolith for interactive APIs and a separately deployable ingestion worker. This retains a small initial service count while allowing ingestion scaling and retry behavior to differ from interactive requests.
2. Use S3 as the source-object store and SQS with a DLQ as the ingestion handoff. The worker must be idempotent and update a durable job state in PostgreSQL.
3. Use Cognito as the initial identity provider, with the API deriving tenant and role from verified claims. Client-supplied tenant identifiers are never authorization evidence.
4. Use PostgreSQL as the source of truth for tenant, document, ingestion, conversation, feedback, and audit metadata. Redis is a disposable cache only.
5. Start with ChromaDB behind an application-owned `VectorStore` port. Keep Chroma-specific schemas and SDK calls in its adapter; evaluate a managed vector service after scale and availability requirements are known.
6. Deploy API and worker as private ECS Fargate services. Isolate ChromaDB as a private stateful service with encrypted durable storage; the exact compute/storage mechanism must be validated before production because ChromaDB persistence and operational scaling are not yet proven.
7. Instrument API and worker with OpenTelemetry-compatible traces, metrics, and structured logs. Use CloudWatch for AWS runtime operations and Langfuse for LLM traces, prompt/version attribution, cost, and feedback, with sensitive content minimized or redacted.

## Project Structure

### Documentation (this feature)

```text
specs\001-rag-hld\
|-- spec.md
|-- plan.md
|-- research.md
|-- quickstart.md
`-- tasks.md
docs\architecture\
|-- overview.md
|-- containers.md
|-- ingestion-sequence.md
|-- online-query-sequence.md
|-- deployment.md
`-- threat-model.md
docs\adr\
|-- 0001-modular-monolith-and-worker.md
|-- 0002-vector-store-boundary.md
`-- 0003-asynchronous-ingestion.md
```

### Runtime Structure (target architecture, not implemented here)

```text
apps\web\                 # React client
apps\api\                 # FastAPI modular monolith
apps\worker\              # asynchronous ingestion and maintenance
packages\domain\          # entities, policies, and ports
packages\application\     # use cases and orchestration
packages\rag\             # retrieval, prompting, citations, guardrails
packages\ingestion\       # parsing, cleaning, chunking, metadata
packages\infrastructure\  # AWS, PostgreSQL, Redis, Chroma, LLM adapters
packages\observability\   # logging, tracing, metrics, cost accounting
packages\evals\           # datasets and evaluators
infra\terraform\          # AWS infrastructure by environment
```

**Structure Decision**: The runtime tree is an architectural target from the source roadmap, not a commitment to create application code in this phase. Architecture documents live under `docs\architecture\` and decisions under `docs\adr\`.

## Deferred Design Artifacts

- Detailed entity fields, database constraints, and job-state transition contracts belong to Phase 2.
- OpenAPI endpoints, event schemas, idempotency keys, pagination, and API error contracts belong to Phase 2.
- Exact AWS region, account topology, SLO numbers, retention, RPO/RTO, model provider, and cost envelope require explicit product/operations decisions.

## Complexity Tracking

No constitution violations or runtime implementation complexity are introduced by this documentation-only feature.

