# Tasks: Phase 4 PDF-to-Cited-Answer Vertical Slice

## Phase 1: API and Local Persistence

- [X] T001 Create API package, local settings, and development-only identity boundary.
- [X] T002 Implement SQLite persistence and local object storage.
- [X] T003 Implement PDF validation, page-aware chunking, and persistent ChromaDB adapter.
- [X] T004 Implement upload intent/upload/completion and document status operations.
- [X] T005 Implement conversations, tenant-filtered retrieval, deterministic mock answer generation, and contract-compatible SSE.

## Phase 2: Web Client

- [X] T006 Create React/TypeScript/Vite application and local login placeholder.
- [X] T007 Implement PDF upload/status and conversation/chat/citation experience.

## Phase 3: Verification and Runbook

- [X] T008 Add focused API integration tests for upload, indexing, idempotency, retrieval, SSE citations, and tenant isolation.
- [X] T009 Update local setup/run instructions and scaffold README status markers.
- [X] T010 Run existing contract tests, API integration tests, frontend build, and inspect git diff for unintended artifacts.

## Acceptance

- A local developer can complete upload -> indexed document -> conversation -> streamed cited answer without external credentials.
- Unsupported or invalid PDFs and unscoped/cross-tenant resource access are rejected.
- Local document and conversation state survive API restart when the same data directory is used.
