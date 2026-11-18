# Product and Architecture Assumptions Log

| ID | Assumption | Status | Validation / owner |
|---|---|---|---|
| A-01 | Initial product is a multi-tenant document assistant; tenant is the primary data-isolation boundary. | Accepted for design | Product/security review before implementation |
| A-02 | Initial roles are tenant administrator, normal user, evaluator, and platform operator. | Accepted for design | Confirm tenant-specific role policy in Phase 2 authorization review |
| A-03 | PDF, DOCX, and PPTX are the first supported document types. | Accepted for MVP | Confirm parser fixture and malformed-file coverage in Phase 5 |
| A-04 | User journeys include upload, status, chat, citation drill-down, feedback, deletion, and evaluation run. | Accepted for MVP | Validate in Phase 4 UX and vertical slice |
| A-05 | API is a modular monolith; ingestion is separately deployable due to different workload and retry needs. | Accepted | ADR-0001; revisit only with measured scaling/ownership need |
| A-06 | AWS is the initial target; React, FastAPI, PostgreSQL, Redis, ChromaDB, S3, SQS, and hosted AI providers follow the source roadmap. | Accepted as target, not provisioned | Confirm provider, region, account, and service availability before IaC |
| A-07 | Cognito is the initial identity option; enterprise federation may front/replace it while preserving server-derived tenant authorization. | Provisional | Identity stakeholder decision before auth implementation |
| A-08 | Tenant scope is derived from validated claims plus server-side membership; browser tenant IDs are selectors only, not authority. | Security invariant | Verify in contract/security tests |
| A-09 | PostgreSQL is authoritative for application metadata and conversation state; S3 is authoritative for original bytes; vectors/cache are derived. | Accepted for design | Revisit deletion and recovery process in implementation |
| A-10 | ChromaDB is a learning/MVP choice behind a vector-store port; production suitability is not yet demonstrated. | Provisional | Benchmark persistence, backup/restore, scaling, and recovery before production |
| A-11 | SSE is used for chat streaming; only validated grounded answer content is user-visible, while progress events may be sent earlier. | Accepted for contract | Verify cancellation, disconnect, and resumability in Phase 4 |
| A-12 | Proposed Phase 0 SLOs represent a low-volume MVP hypothesis and are not contractual. | Provisional | Baseline in staging; review with measured workload and provider pricing |
| A-13 | Exact file-size/page limits, retention, compliance, data residency, model provider, and RPO/RTO are unknown. | Open decision | Product/security/platform owners before production design |
| A-14 | Repository scaffolding and interface artifacts are created before runtime app code; executable vertical slice begins in Phase 4. | Accepted | Keep placeholder READMEs explicit |
| A-15 | The first ingestion-SLO benchmark uses files up to 25 MB and 100 pages/slides. This is not the final upload policy. | Provisional | Measure parser/embedding latency in Phase 5 and approve limits with product/platform owners |
