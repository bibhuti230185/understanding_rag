# Product Brief: Multi-Tenant Document Knowledge Assistant

**Status**: MVP framing; targets are provisional  
**Source**: `RAG_Lucid_AI_Arch.docx`, phases 0-1  
**Related**: [SLO proposals](slo-proposals.md), [assumptions log](assumptions-log.md), [risk register](risk-register.md), [modular-monolith ADR](../adr/0001-modular-monolith-and-worker.md)

## Purpose and Users

Help teams find answers in their own PDF, DOCX, and PPTX files. Answers should be grounded in authorized documents, cite their sources, and disclose when evidence is insufficient.

| Persona | MVP goal |
|---|---|
| Tenant administrator | Manage tenant members/documents; inspect status and failures |
| Normal user | Upload permitted files; ask questions; inspect citations; provide feedback |
| Evaluator | Run approved evaluations and review quality results |
| Platform operator | Maintain service health and recover jobs; access tenant content only through approved, audited break-glass |

Authorization comes from validated identity and server-side tenant membership—not a client-supplied tenant ID.

## MVP Journeys and Scope

Upload a supported file to quarantine; view queued/processing/indexed/failed status; chat over authorized content and inspect cited passages; rate an answer; request document deletion; and run an authorized evaluation.

The initial shape is a React client, modular FastAPI API, separate ingestion worker, PostgreSQL metadata, S3 object storage, SQS/DLQ, optional Redis cache, ChromaDB behind a vector-store port, and hosted embedding/LLM providers. This is a target design, not provisioned infrastructure.

**Non-goals**: microservice-per-context deployment; arbitrary autonomous tool execution; guaranteed enterprise SSO/SCIM or regulatory certification; production commitment to ChromaDB before durability/recovery/scale testing; mobile-native apps; approved production SLOs before baseline measurement.

## Initial Success Measures

Provisional low-volume MVP targets: API availability **99.5% monthly**; p95 retrieval **≤1.5 s**; p95 time to first validated answer token **≤3 s**; **95%** of benchmark documents indexed within **5 min**; citation correctness **≥95%** on a reviewed evaluation set; provider cost **≤$0.15** per defined 10-turn conversation. Definitions and measurement rules are in [SLO proposals](slo-proposals.md). These are hypotheses, not commitments.

## Assumptions and Top Risks

Assume AWS as the initial target; four roles above; PDF/DOCX/PPTX ingestion; PostgreSQL as metadata source of truth; S3 as original-byte source; vectors/cache as derived data; and immediate access revocation with asynchronous deletion cleanup. Exact file limits, identity/model provider, compliance, data residency/retention, workload, and RPO/RTO remain open; see the [assumptions log](assumptions-log.md).

Highest risks are cross-tenant leakage, malicious or prompt-injection documents, incorrect citations, provider cost/latency variability, and self-managed vector-store fragility. Mitigations and review triggers are in the [risk register](risk-register.md).

