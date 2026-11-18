# Tasks: Product Framing, LLD Contracts, and Repository Structure

**Input**: Design documents from `specs\002-product-contracts-structure\`

**Prerequisites**: `plan.md`, `spec.md`, and `research.md`

**Tests**: Validate schemas, Pydantic models, links, and expected scaffold paths; application tests are not part of this feature.

## Phase 1: Product and Architecture Framing (Phase 0)

**Goal**: Define MVP value, personas, journeys, provisional SLOs, assumptions, and risks.

**Independent Test**: Stakeholders can explain the MVP, its users, its success measures, and its highest risks without inferring undocumented scope.

- [X] T001 [US1] Write the product brief, personas, journeys, non-goals, and MVP scope in `docs\product\product-brief.md`
- [X] T002 [US1] Record measurable provisional SLOs and their measurement method in `docs\product\slo-proposals.md`
- [X] T003 [P] [US1] Record assumptions, status, and validation owner in `docs\product\assumptions-log.md`
- [X] T004 [P] [US1] Record ranked product, security, provider, and operations risks in `docs\product\risk-register.md`
- [X] T005 [US1] Link modular-monolith decision to ADR-0001 in `docs\product\product-brief.md`

## Phase 2: LLD and Contracts

**Goal**: Define stable API, entity, event, workflow-state, authorization, error, idempotency, and tracing contracts before application handlers.

**Independent Test**: OpenAPI and JSON Schema parse; Pydantic models validate examples; all API paths and job/event states have explicit tenant and error semantics.

- [X] T006 [US2] Define versioned HTTP endpoints, schemas, and RFC 9457 error responses in `docs\contracts\openapi.yaml`
- [X] T007 [P] [US2] Implement Pydantic v2 transport and workflow DTO schemas in `packages\contracts\python\rag_contracts\models.py`
- [X] T008 [P] [US2] Define entities, relationships, invariants, and job state transitions in `docs\contracts\domain-model.md`
- [X] T009 [P] [US2] Define LangGraph-neutral RAG state and SSE event behavior in `docs\contracts\rag-state.md`
- [X] T010 [P] [US2] Define document lifecycle event envelopes and payload JSON Schemas in `docs\contracts\events.schema.json`
- [X] T011 [P] [US2] Define idempotency, correlation, and trace propagation in `docs\contracts\idempotency-and-tracing.md`
- [X] T012 [P] [US2] Define tenant/role authorization, filters, and cursor pagination in `docs\contracts\authorization-and-pagination.md`
- [X] T013 [US2] Package the shared Pydantic contracts in `packages\contracts\pyproject.toml`
- [X] T014 [US2] Add representative valid/invalid DTO and workflow tests in `tests\contract\test_contract_models.py`
- [X] T015 [US2] Document contract package contents and transport/domain boundary in `packages\contracts\README.md`

## Phase 3: Repository and Solution Structure

**Goal**: Establish navigable monorepo ownership without pretending runtime services or infrastructure are implemented.

**Independent Test**: Every planned app/package/test/infra/docs/CI path exists and has an ownership or purpose marker.

- [X] T016 [US3] Document monorepo layout, frontend/backend modules, and dependency direction in `docs\architecture\repository-structure.md`
- [X] T017 [P] [US3] Add web app ownership and implementation-phase marker in `apps\web\README.md`
- [X] T018 [P] [US3] Add API app ownership and implementation-phase marker in `apps\api\README.md`
- [X] T019 [P] [US3] Add worker ownership and implementation-phase marker in `apps\worker\README.md`
- [X] T020 [P] [US3] Define domain package ownership in `packages\domain\README.md`
- [X] T021 [P] [US3] Define application package ownership in `packages\application\README.md`
- [X] T022 [P] [US3] Define RAG package ownership in `packages\rag\README.md`
- [X] T023 [P] [US3] Define ingestion package ownership in `packages\ingestion\README.md`
- [X] T024 [P] [US3] Define infrastructure adapter ownership in `packages\infrastructure\README.md`
- [X] T025 [P] [US3] Define observability package ownership in `packages\observability\README.md`
- [X] T026 [P] [US3] Define evaluation package ownership in `packages\evals\README.md`
- [X] T027 [P] [US3] Define unit test scope in `tests\unit\README.md`
- [X] T028 [P] [US3] Define integration test scope in `tests\integration\README.md`
- [X] T029 [P] [US3] Define contract test scope in `tests\contract\README.md`
- [X] T030 [P] [US3] Define end-to-end test scope in `tests\e2e\README.md`
- [X] T031 [P] [US3] Define evaluation test scope in `tests\evaluation\README.md`
- [X] T032 [P] [US3] Mark Terraform module ownership and provisioning deferral in `infra\terraform\modules\README.md`
- [X] T033 [P] [US3] Mark development environment scope in `infra\terraform\environments\dev\README.md`
- [X] T034 [P] [US3] Mark staging environment scope in `infra\terraform\environments\staging\README.md`
- [X] T035 [P] [US3] Mark production environment gates in `infra\terraform\environments\prod\README.md`
- [X] T036 [P] [US3] Define runbook area and planned incident guides in `docs\runbooks\README.md`
- [X] T037 [P] [US3] Define interview-notes area and scope in `docs\interview-notes\README.md`
- [X] T038 [P] [US3] Define CI workflow scope and OIDC credential rule in `.github\workflows\README.md`
- [X] T039 [US3] Add repository entry point and phase status in `README.md`

## Dependencies and Execution Order

- Phase 1 (T001-T005) establishes product assumptions and proposed operating targets.
- Phase 2 (T006-T015) follows the Phase 1 HLD and product journeys. Schema/model and policy documents are independent by file.
- Phase 3 (T016-T039) establishes package ownership and can be reviewed alongside contracts; `packages\contracts\` is the integration point for OpenAPI and Pydantic artifacts.
- All phases are documentation/contracts/scaffolding only. Functional service implementation starts in Phase 4.

## MVP

The minimum useful result is T001, T006-T009, and T015: product scope, API/domain/RAG contracts, and a navigable target repository layout. The remaining tasks complete operational, event, testing, and infrastructure boundaries.
